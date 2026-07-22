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
        response_data: dict[str, Any], field_metadata: dict[str, Any], filter_metadata: dict[str, Any] | None = None
    ) -> geojson.FeatureCollection:
        pass


class MetadataTransformer(TransformerABC):
    def get_field_value(self, field_data: dict[str, Any], field_key_mappings: dict[str, Any]) -> Any:
        field_value = deepcopy(field_data)
        for field_key_mapping in field_key_mappings:
            # If None has been reached for the field value then the field is missing from the response
            if field_value is None:
                return field_value

            field_value = field_value.get(field_key_mapping["key"])
            field_type = field_key_mapping["type"]

            if field_type == "list" and isinstance(field_value, list):
                field_value = field_value[field_key_mapping["index"]]
            elif field_type == "wkt_list":
                if field_value is None:
                    print()

                field_value = self.get_geometry_from_wkt_list(field_value)

        return field_value

    def get_geometry_from_wkt_list(self, wkt_list: list[dict[str, Any]]) -> shapely.Point | None:
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

    def check_item_to_be_kept(self, item: dict[str, Any], filter_config: dict[str, Any]) -> bool:
        if filter_config["type"] == "list":
            # It's assumed that there may be multiple entries in the list, but only one matching the expected id
            # field.
            for item_entry in item.get(filter_config["list_field"], []):
                id_value = self.get_field_value(
                    field_data=item_entry, field_key_mappings=filter_config["id_field_keys"]
                )
                if id_value != filter_config["expected_id"]:
                    continue

                # It's assumed that there is only a single entry for the expected id, therefore once the value
                # has been checked, the function can exit and return either True or False to indicate whether the
                # item should be kept
                filter_value = self.get_field_value(
                    field_data=item_entry, field_key_mappings=filter_config["value_field_keys"]
                )
                if filter_value == filter_config["expected_value"]:
                    return True

                return False

    def transform_response(
        self,
        response_data: dict[str, Any],
        field_metadata: dict[str, Any],
        filter_metadata: dict[str, Any] | None = None,
    ) -> geojson.FeatureCollection:
        if not isinstance(field_metadata, list):
            raise ValueError("Unable to transform response, no corresponding field metadata")

        features = []
        for item in response_data.get("items", [{}])[0].get("contains", []):
            if filter_metadata is not None:
                # Assume the filtering configuration is "and", whereby if one of the configs cause the item to fail
                # the filtering checks, the item is considered unwanted
                keep_item = True
                for filter_config in filter_metadata:
                    if not self.check_item_to_be_kept(item=deepcopy(item), filter_config=filter_config):
                        keep_item = False
                        break

                # Skip the current item in the list if it doesn't pass the filtering checks
                if not keep_item:
                    continue

            decoded_item = {}
            for field in field_metadata:
                field_value = self.get_field_value(deepcopy(item), field["field_keys"])
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
