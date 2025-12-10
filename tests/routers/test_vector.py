from pathlib import Path
from typing import Any

import geojson
import pytest
from fastapi.testclient import TestClient

from geospatial_api.main import app

client = TestClient(app)


@pytest.fixture()
def expected_geojson(data_dir: Path) -> dict[str, Any]:
    geojson_path = data_dir.joinpath("test_vector_4326.geojson")
    with open(geojson_path) as geojson_file:
        geojson_data = geojson.load(geojson_file)

    return geojson_data


class TestVector:
    def test_vector_from_s3(self, expected_geojson: dict[str, Any]) -> None:
        """Test the vector endpoint returns valid geojson from s3."""
        response = client.get("/api/vector?url=S3://ukceh-fdri-staging-geospatial/vector/test_vector_4326.geojson")
        assert response.status_code == 200
        assert response.json() == expected_geojson

    def test_vector_from_file_url(self, data_dir: Path, expected_geojson: dict[str, Any]) -> None:
        """Test the vector endpoint returns valid geojson from a file:// url."""
        geojson_path = data_dir.joinpath("test_vector_4326.geojson")
        response = client.get(f"/api/vector?url=file:///{geojson_path}")
        assert response.status_code == 200
        assert response.json() == expected_geojson
