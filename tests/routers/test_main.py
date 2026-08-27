import pytest
from fastapi.testclient import TestClient

from geospatial_api.main import app
from geospatial_api.utils.utils import get_db

client = TestClient(app)


def check_db_available(*args, **kwargs) -> bool:
    """Check if tests need to be skipped if the database isn't available.

    If no error occurs whilst attempting to connect to the database then it returns False (i.e. don't skip tests),
    If any error appears then the test is skipped.
    """
    try:
        db = list(get_db())[0]
        db.connection()
        return False
    except Exception:
        return True


@pytest.mark.skipif(check_db_available(), reason="database is not available")
class TestAvailableData:
    def test_available_data(self) -> None:
        """Test the available_data endpoint returns the expected response."""
        expected_json = [
            {
                "id": 1,
                "name": "Tweed DSM",
                "description": "Digital surface model covering the Tweed catchment",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": "2026-03-20",
                "start_date": None,
                "end_date": None,
                "source_type": {
                    "id": 1,
                    "name": "S3",
                    "object_key": "s3",
                    "base_url": "s3://ukceh-fdri-staging-geospatial",
                },
                "layer_id": None,
                "data_format": {"id": 1, "name": "Raster", "object_key": "raster"},
                "data_category": {
                    "id": 19,
                    "name": "Digital surface model",
                    "object_key": "dsm",
                    "data_category_group": {"id": 6, "name": "Topography and remote sensing", "object_key": "topo_rs"},
                },
                "legend": {
                    "type": "range",
                    "values": [
                        {
                            "min": {"value": 289.97, "colour": [51, 51, 153]},
                            "max": {"value": 291.61, "colour": [14, 126, 228]},
                        },
                        {
                            "min": {"value": 291.61, "colour": [14, 126, 228]},
                            "max": {"value": 293.25, "colour": [1, 188, 148]},
                        },
                        {
                            "min": {"value": 293.25, "colour": [1, 188, 148]},
                            "max": {"value": 294.9, "colour": [85, 221, 119]},
                        },
                        {
                            "min": {"value": 294.9, "colour": [85, 221, 119]},
                            "max": {"value": 296.54, "colour": [197, 243, 141]},
                        },
                        {
                            "min": {"value": 296.54, "colour": [197, 243, 141]},
                            "max": {"value": 298.18, "colour": [226, 218, 137]},
                        },
                        {
                            "min": {"value": 298.18, "colour": [226, 218, 137]},
                            "max": {"value": 299.83, "colour": [170, 146, 107]},
                        },
                        {
                            "min": {"value": 299.83, "colour": [170, 146, 107]},
                            "max": {"value": 301.47, "colour": [143, 112, 105]},
                        },
                        {
                            "min": {"value": 301.47, "colour": [143, 112, 105]},
                            "max": {"value": 303.11, "colour": [199, 183, 180]},
                        },
                        {
                            "min": {"value": 303.11, "colour": [199, 183, 180]},
                            "max": {"value": 304.76, "colour": [199, 195, 195]},
                        },
                    ],
                },
                "bbox": {"min_x": -3.417467, "max_x": -3.417269, "min_y": 55.510475, "max_y": 55.510617},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 2,
                    "name": "Tweed",
                    "object_key": "tweed",
                    "location_type": {"id": 2, "name": "Catchment", "object_key": "catchment"},
                    "bbox": {"min_x": -3.417466, "max_x": -3.41727, "min_y": 55.510476, "max_y": 55.510616},
                    "centroid": {"x": -3.4173733172561627, "y": 55.51054843676313},
                },
                "field_metadata": None,
                "filter_metadata": None,
                "resource_metadata": None,
                "map_center": [-3.417368, 55.510546],
                "colour_source_url": (
                    "s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=catchment/location=tweed/"
                    "data_category=dsm/processing_level=processed/date=2026-03-20/"
                    "clipped_tweed_dsm_3857_colourised_cog.tif"
                ),
                "raw_source_url": (
                    "s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=catchment/location=tweed/"
                    "data_category=dsm/processing_level=processed/date=2026-03-20/"
                    "clipped_tweed_dsm_3857_greyscale_cog.tif"
                ),
            },
            {
                "id": 2,
                "name": "Cosmos Sites",
                "description": None,
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": "2026-03-20",
                "end_date": "2026-05-01",
                "source_type": {
                    "id": 2,
                    "name": "Metadata API",
                    "object_key": "metadata_api",
                    "base_url": "https://dri-metadata-api.staging.dri.ceh.ac.uk",
                },
                "layer_id": None,
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 5,
                    "name": "Soil moisture",
                    "object_key": "soil_moisture",
                    "data_category_group": {"id": 2, "name": "Soils", "object_key": "soils"},
                },
                "legend": None,
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": [
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "ID",
                        "key": "id",
                        "field_keys": [{"key": "identifier", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Altitude",
                        "key": "altitude",
                        "field_keys": [{"key": "altitude", "type": "value"}],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Start Date",
                        "key": "start_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "startDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "End date",
                        "key": "end_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "endDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                "filter_metadata": None,
                "resource_metadata": [
                    {
                        "level": "feature",
                        "url": "https://dri-ui.staging.dri.ceh.ac.uk/fdri/timeseries?network=cosmos&site={site_id}",
                        "url_mapping": {"site_id": "id"},
                        "label": "timeseries data",
                    }
                ],
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": (
                    "https://dri-metadata-api.staging.dri.ceh.ac.uk/id/network/cosmos?_projection=contains.label,"
                    "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                    "contains.altitude"
                ),
            },
            {
                "id": 3,
                "name": "EA Flow Gaugings",
                "description": None,
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": "2024-01-01",
                "end_date": None,
                "source_type": {
                    "id": 2,
                    "name": "Metadata API",
                    "object_key": "metadata_api",
                    "base_url": "https://dri-metadata-api.staging.dri.ceh.ac.uk",
                },
                "layer_id": None,
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 11,
                    "name": "Flow monitoring",
                    "object_key": "flow_monitoring",
                    "data_category_group": {"id": 4, "name": "Hydrology", "object_key": "hydrology"},
                },
                "legend": None,
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 2, "name": "Raw", "object_key": "raw"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": [
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Name",
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                "filter_metadata": None,
                "resource_metadata": None,
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": (
                    "https://dri-metadata-api.staging.dri.ceh.ac.uk/id/network/ea-manual-flow?"
                    "_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*,"
                    "contains.operatingPeriod.*,contains.altitude"
                ),
            },
            {
                "id": 4,
                "name": "Landcover map",
                "description": "2024 Landcover map (GB)",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": "2024-01-01",
                "end_date": None,
                "source_type": {
                    "id": 3,
                    "name": "EIDC Catalogue WMS",
                    "object_key": "eidc_wms",
                    "base_url": "https://catalogue.ceh.ac.uk/maps",
                },
                "layer_id": "wms",
                "data_format": {"id": 3, "name": "Web Map Services", "object_key": "wms"},
                "data_category": {
                    "id": 23,
                    "name": "Land cover",
                    "object_key": "land_cover",
                    "data_category_group": {"id": 8, "name": "Land cover", "object_key": "land_cover"},
                },
                "legend": {
                    "type": "category",
                    "values": [
                        {"value": "Suburban", "colour": [128, 128, 128]},
                        {"value": "Urban", "colour": [0, 0, 0]},
                        {"value": "Saltmarsh", "colour": [128, 128, 255]},
                        {"value": "Littoral sediment", "colour": [255, 255, 128]},
                        {"value": "Littoral rock", "colour": [255, 255, 128]},
                        {"value": "Supra-littoral sediment", "colour": [204, 179, 0]},
                        {"value": "Supra-littoral rock", "colour": [152, 125, 183]},
                        {"value": "Freshwater", "colour": [0, 0, 255]},
                        {"value": "Saltwater", "colour": [0, 0, 92]},
                        {"value": "Inland rock", "colour": [210, 210, 255]},
                        {"value": "Bog", "colour": [205, 29, 181]},
                        {"value": "Heather grassland", "colour": [230, 140, 166]},
                        {"value": "Heather", "colour": [128, 26, 128]},
                        {"value": "Fen, marsh and swamp", "colour": [253, 123, 238]},
                        {"value": "Acid grassland", "colour": [178, 145, 0]},
                        {"value": "Calcareous grassland", "colour": [255, 192, 55]},
                        {"value": "Neutral grassland", "colour": [220, 153, 9]},
                        {"value": "Improved grassland", "colour": [1, 255, 124]},
                        {"value": "Arable and horticulture", "colour": [240, 228, 66]},
                        {"value": "Coniferous woodland", "colour": [0, 80, 0]},
                        {"value": "Broadleaved, mixed and yew woodland", "colour": [51, 160, 44]},
                    ],
                },
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 2, "name": "Raw", "object_key": "raw"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": None,
                "filter_metadata": None,
                "resource_metadata": [
                    {
                        "level": "layer",
                        "url": "https://catalogue.ceh.ac.uk/",
                        "url_mapping": {},
                        "label": "EIDC catalogue",
                    }
                ],
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": "https://catalogue.ceh.ac.uk/maps/76405b92-17ec-4ed2-ac7f-17caeb2d14f6",
            },
            {
                "id": 5,
                "name": "UKCEH river network",
                "description": None,
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": None,
                "end_date": None,
                "source_type": {
                    "id": 4,
                    "name": "Hydrology Geoserver WMS",
                    "object_key": "hydrology_geoserver",
                    "base_url": "https://hydrologygeoserver.ceh.ac.uk/geoserver/wms",
                },
                "layer_id": "river_vectors%3AIRN_riverLine",
                "data_format": {"id": 3, "name": "Web Map Services", "object_key": "wms"},
                "data_category": {
                    "id": 13,
                    "name": "River network",
                    "object_key": "river_network",
                    "data_category_group": {"id": 4, "name": "Hydrology", "object_key": "hydrology"},
                },
                "legend": None,
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": None,
                "filter_metadata": None,
                "resource_metadata": None,
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": "https://hydrologygeoserver.ceh.ac.uk/geoserver/wms/river_vectors",
            },
            {
                "id": 6,
                "name": "EA river flow stations",
                "description": "EA river flow stations in the area of the Chess",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": "1934-02-28",
                "end_date": None,
                "source_type": {
                    "id": 2,
                    "name": "Metadata API",
                    "object_key": "metadata_api",
                    "base_url": "https://dri-metadata-api.staging.dri.ceh.ac.uk",
                },
                "layer_id": None,
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 9,
                    "name": "River flow",
                    "object_key": "river_flow",
                    "data_category_group": {"id": 4, "name": "Hydrology", "object_key": "hydrology"},
                },
                "legend": None,
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": [
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": None,
                        "key": "id",
                        "field_keys": [
                            {"key": "identifier", "type": "id_dict", "id_field": "wiskiID", "separator": "|"}
                        ],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Altitude",
                        "key": "altitude",
                        "field_keys": [{"key": "altitude", "type": "value"}],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Start Date",
                        "key": "start_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "startDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "End date",
                        "key": "end_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "endDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": None,
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                "filter_metadata": [
                    {
                        "type": "list",
                        "list_field": "hasAnnotation",
                        "id_field_keys": [{"key": "property", "type": "value"}, {"key": "@id", "type": "value"}],
                        "value_field_keys": [
                            {"key": "hasValue", "type": "value"},
                            {"key": "value", "type": "list", "index": 0},
                        ],
                        "expected_id": "http://fdri.ceh.ac.uk/ref/common/annotation-property/isChess",
                        "expected_value": True,
                    }
                ],
                "resource_metadata": None,
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": (
                    "https://dri-metadata-api.staging.dri.ceh.ac.uk/id/network/ea-flow.json?_view=extended&"
                    "_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*,"
                    "contains.operatingPeriod.*,contains.altitude,contains.hasAnnotation.*&_withView"
                ),
            },
            {
                "id": 7,
                "name": "Plynlimon monthly rain gauges",
                "description": "",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": None,
                "start_date": "1934-02-28",
                "end_date": None,
                "source_type": {
                    "id": 2,
                    "name": "Metadata API",
                    "object_key": "metadata_api",
                    "base_url": "https://dri-metadata-api.staging.dri.ceh.ac.uk",
                },
                "layer_id": None,
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 15,
                    "name": "Rainfall",
                    "object_key": "rainfall",
                    "data_category_group": {
                        "id": 5,
                        "name": "Meteorology and climate",
                        "object_key": "meteorology_climate",
                    },
                },
                "legend": None,
                "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "location_type": {"id": 1, "name": "National", "object_key": "national"},
                    "bbox": {"min_x": -7.291954, "max_x": 1.034231, "min_y": 50.03266, "max_y": 56.914403},
                    "centroid": {"x": -3.1288614999999993, "y": 53.4735315},
                },
                "field_metadata": [
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": None,
                        "key": "id",
                        "field_keys": [
                            {"key": "identifier", "type": "id_dict", "id_field": "wiskiID", "separator": "|"}
                        ],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Altitude",
                        "key": "altitude",
                        "field_keys": [{"key": "altitude", "type": "value"}],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Start Date",
                        "key": "start_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "startDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "End date",
                        "key": "end_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "endDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": None,
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Aspect",
                        "key": "aspect",
                        "field_keys": [
                            {
                                "key": "hasAnnotation",
                                "type": "annotation",
                                "id_value": "http://fdri.ceh.ac.uk/ref/common/annotation-property/aspect",
                            }
                        ],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Gauge Type",
                        "key": "gauge_type",
                        "field_keys": [
                            {
                                "key": "hasAnnotation",
                                "type": "annotation",
                                "id_value": "http://fdri.ceh.ac.uk/ref/common/annotation-property/gauge_type",
                            }
                        ],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Slope",
                        "key": "slope",
                        "field_keys": [
                            {
                                "key": "hasAnnotation",
                                "type": "annotation",
                                "id_value": "http://fdri.ceh.ac.uk/ref/common/annotation-property/slope",
                            }
                        ],
                        "data_type": "float",
                    },
                ],
                "filter_metadata": None,
                "resource_metadata": None,
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": (
                    "https://dri-metadata-api.staging.dri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.json?"
                    "_view=extended&_projection=contains.label,contains.comment,contains.identifier,"
                    "contains.hasGeometry.*,contains.operatingPeriod.*,contains.altitude,contains.hasAnnotation.*"
                    "&_withView"
                ),
            },
        ]
        response = client.get("public/api/available_data")

        assert response.status_code == 200
        assert response.json() == expected_json
