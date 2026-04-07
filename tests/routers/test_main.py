from fastapi.testclient import TestClient

from geospatial_api.main import app

client = TestClient(app)


class TestAvailableData:
    def test_available_data(self) -> None:
        """Test the available_data endpoint returns the expected response."""
        expected_json = [
            {
                "id": 1,
                "name": "Tweed DSM",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": "2026-03-20",
                "source_type": {
                    "id": 1,
                    "name": "S3",
                    "object_key": "s3",
                    "base_url": "s3://ukceh-fdri-staging-geospatial",
                },
                "catalogue_id": None,
                "data_format": {"id": 1, "name": "Raster", "object_key": "raster"},
                "data_category": {"id": 2, "name": "DSM", "object_key": "dsm"},
                "legend": [
                    {"value": 289.97, "colour": [51, 51, 153]},
                    {"value": 291.61, "colour": [14, 126, 228]},
                    {"value": 293.25, "colour": [1, 188, 148]},
                    {"value": 294.9, "colour": [85, 221, 119]},
                    {"value": 296.54, "colour": [197, 243, 141]},
                    {"value": 298.18, "colour": [226, 218, 137]},
                    {"value": 299.83, "colour": [170, 146, 107]},
                    {"value": 301.47, "colour": [143, 112, 105]},
                    {"value": 303.11, "colour": [199, 183, 180]},
                    {"value": 304.76, "colour": [199, 195, 195]},
                ],
                "bbox": (
                    "POLYGON ((-3.417467 55.510475, -3.417269 55.510475, -3.417269 55.510617, -3.417467 55.510617, "
                    "-3.417467 55.510475))"
                ),
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "area_name": {
                    "id": 2,
                    "name": "Tweed",
                    "object_key": "tweed",
                    "area_type": {"id": 3, "name": "Catchment", "object_key": "catchment"},
                },
                "map_center": [-3.417368, 55.510546],
                "colour_source_url": (
                    "s3://ukceh-fdri-staging-geospatial/project=fdri/area_type=catchment/area_name=tweed/"
                    "data_category=dsm/processing_level=processed/date=2026-03-20/"
                    "clipped_tweed_dsm_3857_colourised_cog.tif"
                ),
                "raw_source_url": None,
            },
            {
                "id": 2,
                "name": "Cosmos Sites",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": "2026-03-20",
                "source_type": {
                    "id": 1,
                    "name": "S3",
                    "object_key": "s3",
                    "base_url": "s3://ukceh-fdri-staging-geospatial",
                },
                "catalogue_id": None,
                "data_format": {"id": 2, "name": "Vector", "object_key": "vector"},
                "data_category": {"id": 3, "name": "Stations", "object_key": "stations"},
                "legend": None,
                "bbox": (
                    "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                    "-7.291954 50.03266))"
                ),
                "processing_level": {"id": 1, "name": "Processed", "object_key": "processed"},
                "area_name": {
                    "id": 1,
                    "name": "UK",
                    "object_key": "uk",
                    "area_type": {"id": 1, "name": "National", "object_key": "national"},
                },
                "map_center": [-3.1288614999999993, 53.4735315],
                "colour_source_url": None,
                "raw_source_url": (
                    "s3://ukceh-fdri-staging-geospatial/project=fdri/area_type=national/area_name=uk/"
                    "data_category=stations/processing_level=processed/date=2026-03-20/cosmos_sites.geojson"
                ),
            },
        ]

        response = client.get("/api/available_data")

        assert response.status_code == 200
        assert response.json() == expected_json
