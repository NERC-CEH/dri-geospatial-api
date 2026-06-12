from typing import Any
from urllib.parse import urlparse

import geojson
from fastapi import APIRouter, Depends, HTTPException
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session

from geospatial_api.services.rds.db import LayerRegistryInterface
from geospatial_api.utils.utils import get_db, get_file_path, get_s3_client
from geospatial_api.utils.vector_https_utils import fetch_vector_data_from_https

public_router = APIRouter(tags=["Vector Data"])
s3 = get_s3_client()


@public_router.get("/vector")
def read_index(
    url: str, layer_id: int | None = None, s3_client: S3Client = Depends(lambda: s3), db: Session = Depends(get_db)
) -> dict[str, Any]:
    url_parts = urlparse(url)

    layer = None
    if layer_id is not None:
        layer = LayerRegistryInterface.get_single_layer(session=db, layer_id=layer_id)

    if url_parts.scheme.lower() == "s3":
        response = s3_client.get_object(Bucket=url_parts.netloc, Key=url_parts.path.lstrip("/"))
        geojson_data = geojson.load(response["Body"])
    elif url_parts.scheme.lower() == "https":
        if layer_id is None:
            raise HTTPException(
                "A layer id must be provided when sourcing vector data from https. No transformation schema available"
            )
        geojson_data = fetch_vector_data_from_https(url=url, layer=layer)

    else:
        file_path = get_file_path(url, s3_client)
        with open(file_path) as geojson_file:
            geojson_data = geojson.load(geojson_file)

    return geojson_data
