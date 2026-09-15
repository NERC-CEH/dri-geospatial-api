import logging
from typing import Any

import requests
from httpx import HTTPError

from geospatial_api.models import Layer
from geospatial_api.utils.transformers import MetadataTransformer

logger = logging.getLogger(__name__)

TRANSFORMER_MAPPING = {"metadata_api": MetadataTransformer}


def fetch_data(url: str) -> dict[str, Any]:
    session = requests.Session()

    try:
        response = session.get(url=url, timeout=30)
        response.raise_for_status()
        return response.json()
    except HTTPError as e:
        logger.error(f"Failed to fetch data: {e}")
        raise
    except ValueError:
        logger.error(f"Invalid JSON response from: {url}")
        raise


def fetch_vector_data_from_https(url: str, layer: Layer) -> dict[str, Any]:
    response_data = fetch_data(url)

    transformer_class = TRANSFORMER_MAPPING.get(layer.source_type.object_key)
    if transformer_class is None:
        raise ValueError("The source type of the layer is not supported")

    if layer.field_metadata is None:
        raise ValueError("Field metadata information is required to construct the geojson data.")

    transformer = transformer_class()

    geojson_data = transformer.transform_response(
        response_data=response_data,
        field_metadata=layer.field_metadata,
        filter_metadata=layer.filter_metadata,
        resource_metadata=layer.resource_metadata,
    )

    return geojson_data
