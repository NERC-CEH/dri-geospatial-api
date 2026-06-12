from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from geospatial_api.main import api, app
from geospatial_api.routers.docs import get_api_root

client = TestClient(app)

_PATCH_TARGET = "geospatial_api.routers.docs.check_ip_address_is_whitelisted"


class TestGetApiRoot:
    def test_returns_root_path_from_scope(self) -> None:
        """Test that the root_path value is extracted from the request scope."""
        request = MagicMock()
        request.scope = {"root_path": "/api"}

        assert get_api_root(request) == "/api"

    def test_returns_empty_string_when_root_path_absent(self) -> None:
        """Test that an empty string is returned when root_path is not in the scope."""
        request = MagicMock()
        request.scope = {}

        assert get_api_root(request) == ""


class TestDocsEndpoint:
    def test_returns_html_response(self) -> None:
        """Test the /docs endpoint returns an HTML page."""
        response = client.get("/api/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_html_references_openapi_json(self) -> None:
        """Test the docs HTML references the openapi.json schema endpoint."""
        response = client.get("/api/docs")

        assert "openapi.json" in response.text


class TestOpenApiEndpoint:
    def test_schema_contains_required_fields(self) -> None:
        """Test the schema has the expected top-level OpenAPI fields."""
        with patch(_PATCH_TARGET, return_value=False):
            response = client.get("/api/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "info" in schema
        assert "paths" in schema
        assert schema["info"]["title"] == api.title

    def test_schema_includes_server_entry(self) -> None:
        """Test the schema includes a servers entry for correct base URL resolution."""
        with patch(_PATCH_TARGET, return_value=False):
            response = client.get("/api/openapi.json")

        assert "servers" in response.json()

    @pytest.mark.parametrize(
        "path",
        [
            "/list_model",
            "/add_model",
            "/add_data_category",
            "/add_location",
            "/add_layer",
        ],
        ids=["list model", "add model", "add data category", "add location", "add layer"],
    )
    def test_each_private_route_excluded_for_non_whitelisted_ip(self, path: str) -> None:
        """Test that each known private route is absent from the public schema."""
        with patch(_PATCH_TARGET, return_value=False):
            response = client.get("/api/openapi.json")

        assert path not in response.json()["paths"]

    @pytest.mark.parametrize(
        "path",
        [
            "/healthcheck/",
            "/available_data",
            "/location_boundary",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
            "/maps/tiles/{z}/{x}/{y}@{scale}x.{format}",
            "/maps/tiles/{z}/{x}/{y}@{scale}x",
            "/maps/tiles/{z}/{x}/{y}.{format}",
            "/maps/tiles/{z}/{x}/{y}",
            "/maps/wms",
            "/maps/validate",
            "/maps/viewer",
            "/vector",
        ],
        ids=[
            "/healthcheck/",
            "/available_data",
            "/location_boundary",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}",
            "/maps/tiles/{tileMatrixSetId}/{z}/{x}/{y}",
            "/maps/tiles/{z}/{x}/{y}@{scale}x.{format}",
            "/maps/tiles/{z}/{x}/{y}@{scale}x",
            "/maps/tiles/{z}/{x}/{y}.{format}",
            "/maps/tiles/{z}/{x}/{y}",
            "/maps/wms",
            "/maps/validate",
            "/maps/viewer",
            "/vector",
        ],
    )
    def test_each_public_route_present_for_non_whitelisted_ip(self, path: str) -> None:
        """Test that each known public route is present in the public schema."""
        with patch(_PATCH_TARGET, return_value=False):
            response = client.get("/api/openapi.json")

        assert path in response.json()["paths"]
