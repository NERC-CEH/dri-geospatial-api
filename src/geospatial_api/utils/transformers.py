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
        """
        Decode a single metadata field value from a nested metadata response. Detailed information about the
        dictionary structure and logic can be found here
        https://github.com/NERC-CEH/fdri_words/blob/main/geospatial/layer_management.md#field-metadata

        The decoding works through the metadata dictionary, decoding each level recursively until the end of the
        list of field key mappings has been reached or the field value is None. The latter indicating that no metadata
        value has been provided for the field in this instance.

        Args:
            field_data: The initial metadata field value dictionary to be decoded.
            field_key_mappings: A list of dictionaries describing each field to be decoded, with the first item in the
                list representing the top level, the next item the level below etc.

        Returns:
            Decoded field value. This is expected to be a single value or None

        """
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
                field_value = self.get_geometry_from_wkt_list(field_value)

        return field_value

    def get_geometry_from_wkt_list(self, wkt_list: list[dict[str, Any]]) -> shapely.Point | None:
        """Extract the WGS84 point geometry from the relevant WKT string in the metadata response

        Args:
            wkt_list: Metadata response from "hasGeometry" field containing the list of WKT strings and their
            corresponding configuration

        returns:
            shapely.Point geometry constructed from the WKT string if it is able to be found. If no suitable WKT is
                found then None is returned.

        """
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
        """
        Applies a single filter configuration to a metadata response item determining whether the item's values
        pass the filter test.

        The expected structure of the filter config is

        {
                    "type":  Type of filter config. Currently  only "list" is supported
                    "list_field": Name of the top level field to fetch the metadata values from. For example
                        "hasAnnotation". It is expected for this to be a list, from which each entry is iterated over
                        and checked against the filter criteria.
                    "id_field_keys": Field metadata for decoding the id field. For example
                        [{"key": "property", "type": "value"}, {"key": "@id", "type": "value"}]
                        It is expected that the format of this field matches the "field_metadata" structure
                        The extracted ID value will then be used to identify if the list entry is one that has a
                        corresponding filter value (e.g. if there are multiple annotations, but only one provides
                        the filtering criteria)
                    "value_field_keys": Similar to "id_field_keys" this provides the field metadata for decoding the
                        field containing the filtering value. The format should match that of the "field_metadata"
                        structure.
                    ],
                    "expected_id": The id field value to apply the filtering for. For example,
                         "http://fdri.ceh.ac.uk/ref/common/annotation/isChess",
                    "expected_value": The corresponding "pass" value which indicates if the metadata item should
                        be kept. For example `True`.
                }
        }

        Args:
            item: Dictionary containing a single metadata item from the "contains" part of the items list
            filter_config: Configuration describing the filter criteria

        Returns:
            True/False indication as to whether to keep the metadata item

        """
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
        else:
            raise ValueError(f"The filter config type `{filter_config['type']}` is not supported.")

    def transform_response(
        self,
        response_data: dict[str, Any],
        field_metadata: dict[str, Any],
        filter_metadata: dict[str, Any] | None = None,
    ) -> geojson.FeatureCollection:
        """
        Transforms the metadata response into a geojson FeatureCollection object ready to be rendered by the UI.

        Args:
            response_data: Metadata response dictionary to be decoded
            field_metadata: Configuration information denoting how to decode individual fields from the metadata
                response, including the key they will be stored under in the geojson feature's properties.
            filter_metadata: Optional set of configurations to filter the metadata response on if required.
                Defaults to None.

        Raises:
            ValueError: No field metadata is provided, or it is not a list

        Returns:
            Geojson FeatureCollection where each feature corresponds to a single item in the metadata response. Any
            required fields are stored as properties alongside the feature geometry.

        """
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
