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
                "data_format": {"id": 1, "name": "Raster", "object_key": "raster"},
                "data_category": {
                    "id": 2,
                    "name": "Digital Surface Model",
                    "object_key": "dsm",
                    "data_category_group": {"id": 1, "name": "Topography and Remote Sensing", "object_key": "topo_rs"},
                },
                "legend": {
                    "type": "range",
                    "values": [
                        {
                            "min": {"label": 289.97, "colour": [51, 51, 153]},
                            "max": {"label": 291.61, "colour": [14, 126, 228]},
                        },
                        {
                            "min": {"label": 291.61, "colour": [14, 126, 228]},
                            "max": {"label": 293.25, "colour": [1, 188, 148]},
                        },
                        {
                            "min": {"label": 293.25, "colour": [1, 188, 148]},
                            "max": {"label": 294.9, "colour": [85, 221, 119]},
                        },
                        {
                            "min": {"label": 294.9, "colour": [85, 221, 119]},
                            "max": {"label": 296.54, "colour": [197, 243, 141]},
                        },
                        {
                            "min": {"label": 296.54, "colour": [197, 243, 141]},
                            "max": {"label": 298.18, "colour": [226, 218, 137]},
                        },
                        {
                            "min": {"label": 298.18, "colour": [226, 218, 137]},
                            "max": {"label": 299.83, "colour": [170, 146, 107]},
                        },
                        {
                            "min": {"label": 299.83, "colour": [170, 146, 107]},
                            "max": {"label": 301.47, "colour": [143, 112, 105]},
                        },
                        {
                            "min": {"label": 301.47, "colour": [143, 112, 105]},
                            "max": {"label": 303.11, "colour": [199, 183, 180]},
                        },
                        {
                            "min": {"label": 303.11, "colour": [199, 183, 180]},
                            "max": {"label": 304.76, "colour": [199, 195, 195]},
                        },
                    ],
                },
                "bbox": {"min_x": -3.417467, "max_x": -3.417269, "min_y": 55.510475, "max_y": 55.510617},
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "location": {
                    "id": 2,
                    "name": "Tweed",
                    "object_key": "tweed",
                    "location_type": {"id": 3, "name": "Catchment", "object_key": "catchment"},
                    "bbox": {"min_x": -3.417466, "max_x": -3.41727, "min_y": 55.510476, "max_y": 55.510616},
                    "centroid": {"x": -3.4173733172561627, "y": 55.51054843676313},
                },
                "field_metadata": None,
                "map_center": [-3.417368, 55.510546],
                "colour_source_url": "s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=catchment/location=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/clipped_tweed_dsm_3857_colourised_cog.tif",
                "raw_source_url": None,
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
                    "base_url": "https://dri-metadata-api.dri.ceh.ac.uk",
                },
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 3,
                    "name": "Soil Moisture",
                    "object_key": "soil_moisture",
                    "data_category_group": {"id": 2, "name": "Geology and Soils", "object_key": "geology_soils"},
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
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": "https://dri-metadata-api.dri.ceh.ac.uk/id/network/cosmos?_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*",
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
                    "base_url": "https://dri-metadata-api.dri.ceh.ac.uk",
                },
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {
                    "id": 4,
                    "name": "Flow Monitoring",
                    "object_key": "flow_monitoring",
                    "data_category_group": {"id": 3, "name": "Hydrology", "object_key": "hydrology"},
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
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": "https://dri-metadata-api.dri.ceh.ac.uk/id/network/ea-manual-sites?_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*",
            },
        ]

        response = client.get("/api/available_data")

        assert response.status_code == 200
        assert response.json() == expected_json
