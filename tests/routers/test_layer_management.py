from datetime import date
from unittest.mock import patch

import dri_database_models.geospatial as db_models
import pytest
from fastapi.testclient import TestClient
from httpx import Request, Response

from geospatial_api.main import app
from geospatial_api.models import SourceType
from geospatial_api.services.rds.db import (
    DataCategoryModelInterface,
    IDModelInterface,
)

client = TestClient(app)


class TestListModel:
    def test_list_model(self) -> None:
        expected_json = [{"id": 1, "name": "S3", "object_key": "s3", "base_url": "http://base_url.com"}]
        with (
            patch("requests.Session.get") as mock_get,
            patch.object(IDModelInterface, "get_db_entries") as mock_db_interface,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json={}, request=mock_request)
            mock_get.return_value = mock_response
            mock_db_interface.return_value = [
                SourceType(
                    id=1, name="S3", object_key="s3", last_updated=date(2026, 1, 1), base_url="http://base_url.com"
                )
            ]

            response = client.get("/api/list_model?model_name=source_type")

        assert response.status_code == 200
        assert response.json() == expected_json

    def test_list_model_no_model_mapping(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(status_code=504, request=mock_request)
            mock_get.return_value = mock_response

            with pytest.raises(ValueError):
                client.get("/api/list_model?model_name=invalid_model")


class TestAddModel:
    def test_add_model(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
            patch.object(IDModelInterface, "add_model_entry") as mock_add_model,
        ):
            mock_request = Request(method="post", url="http://test_url.com")
            mock_response = Response(200, json={}, request=mock_request)
            mock_get.return_value = mock_response
            mock_add_model.return_value = db_models.DataFormat(
                id=1,
                last_updated=date(2026, 1, 1),
                name="GeoJSON",
                object_key="geojson",
            )

            response = client.post("/api/add_model?model_name=data_format&name=GeoJSON&object_key=geojson")

        assert response.status_code == 200
        assert response.json() == "Successfully created data_format GeoJSON"

    def test_add_model_no_model_mapping(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
        ):
            mock_request = Request(method="post", url="http://test_url.com")
            mock_response = Response(status_code=504, request=mock_request)
            mock_get.return_value = mock_response

            with pytest.raises(ValueError):
                client.post("/api/add_model?model_name=invalid_model&name=GeoJSON&object_key=geojson")


class TestAddDataCategory:
    def test_add_data_category(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
            patch.object(DataCategoryModelInterface, "add_new_entry") as mock_db_interface,
        ):
            mock_request = Request(method="post", url="http://test_url.com")
            mock_response = Response(200, json={}, request=mock_request)
            mock_get.return_value = mock_response
            mock_db_interface.return_value = db_models.DataCategory(
                id=1, last_updated=date(2026, 1, 1), name="Category 1", object_key="category_1", data_category_group=1
            )

            response = client.post("/api/add_data_category?name=Category 1&object_key=category_1&category_group_key=1")

        assert response.status_code == 200
        assert response.json() == "Successfully created new data category Category 1"
