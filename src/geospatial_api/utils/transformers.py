import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

import geojson
import shapely

logger = logging.getLogger(__name__)


class TransformerABC(ABC):
    @abstractmethod
    def transform_response(
        response_data: dict[str | Any], field_metadata: dict[str | Any]
    ) -> geojson.FeatureCollection:
        pass


class MetadataTransformer(TransformerABC):
    @staticmethod
    def get_field_value(field_data: dict[str | Any], field_key_mappings: dict[str | Any]) -> Any:
        field_value = deepcopy(field_data)
        for field_key_mapping in field_key_mappings:
            field_value = field_value.get(field_key_mapping["key"])
            field_type = field_key_mapping["type"]

            if field_type == "list":
                field_value = field_value[field_key_mapping["index"]]
            elif field_type == "wkt_list":
                field_value = MetadataTransformer.get_geometry_from_wkt_list(field_value)

        return field_value

    @staticmethod
    def get_geometry_from_wkt_list(wkt_list: list[dict[str | Any]]) -> shapely.Point | None:
        geometry = None
        for wkt in wkt_list:
            wkt_str = wkt.get("asWKT")
            if not wkt_str:
                continue

            if "<http://www.opengis.net/def/crs/EPSG/0/27700>" in wkt_str:
                continue
            else:
                # WGS84 coordinates
                try:
                    geometry = shapely.wkt.loads(wkt_str)
                    return geometry
                except shapely.errors.GEOSException:
                    continue

        return geometry

    @staticmethod
    def transform_response(
        response_data: dict[str | Any], field_metadata: dict[str | Any]
    ) -> geojson.FeatureCollection:
        if not isinstance(field_metadata, list):
            raise ValueError("Unable to transform response, no corresponding field metadata")

        features = []
        for item in response_data.get("items", [{}])[0].get("contains", []):
            decoded_item = {}
            for field in field_metadata:
                field_value = MetadataTransformer.get_field_value(item, field["field_keys"])
                decoded_item[field["key"]] = field_value

            # Convert to geojson feature
            geometry = decoded_item.get("geometry")
            if geometry is None:
                logger.info("Skipping entry, no geometry information available")
                continue

            features.append(
                geojson.Feature(
                    geometry=geometry,
                    properties={key: value for (key, value) in decoded_item.items() if key != "geometry"},
                )
            )

        return geojson.FeatureCollection(features)
