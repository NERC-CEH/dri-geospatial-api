from fastapi.testclient import TestClient

from geospatial_api.main import app

client = TestClient(app)


class TestAvailableData:
    def test_available_data(self) -> None:
        """Test the available_data endpoint returns the expected response."""
        expected_json = [
            {
                "id": 0,
                "name": "test_raster_3857_cog_greyscale",
                "data_type": "raster",
                "s3_url": "S3://ukceh-fdri-staging-geospatial/raster/test_raster_3857_cog_greyscale.tif",
                "geojson": None,
                "map_centre": [54.008128, -2.774925],
                "colourmap_name": "terrain",
            },
            {
                "id": 1,
                "name": "test_raster_3857_cog_rendered",
                "data_type": "raster",
                "s3_url": "S3://ukceh-fdri-staging-geospatial/raster/test_raster_3857_cog_rendered.tif",
                "geojson": None,
                "map_centre": [54.008128, -2.774925],
                "colourmap_name": None,
            },
            {
                "id": 2,
                "name": "test_vector_4326",
                "data_type": "vector",
                "s3_url": "S3://ukceh-fdri-staging-geospatial/vector/test_vector_4326.geojson",
                "geojson": None,
                "map_centre": [54.008128, -2.774925],
                "colourmap_name": None,
            },
        ]

        response = client.get("/api/available_data")

        assert response.status_code == 200
        assert response.json() == expected_json
