"""Tests for the mount-driven ``/public`` and ``/private`` v1 route trees."""

import pytest
from fastapi.testclient import TestClient

from geospatial_api.main import app

client = TestClient(app)


class TestPublicTree:
    """``/public/api`` always serves the limited view."""

    def test_healthcheck_reachable(self) -> None:
        """The health check stays reachable on the public tree."""
        response = client.get("/public/api/healthcheck/")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.parametrize(
        "route",
        [
            "list_model?model_name=project",
            "add_model?model_name=project&object_key=fdri",
            "update_model?model_id=1&model_name=project&object_key=fdri",
            "add_source_type?name=Test&object_key=test&base_url=http://example.com",
            "update_source_type?model_id=1&name=Test&object_key=test&base_url=http://example.com",
            "add_data_category?name=Test&object_key=test&category_group_key=test",
            "update_data_category?model_id=1&name=Test&object_key=test&category_group_key=test",
            "add_location?name=Test&object_key=test&categolocation_type_key=test",
            "update_location?model_id=1&name=Test&object_key=test&categolocation_type_key=test",
            "add_layer",
            "update_layer",
            "clear_layer_field",
        ],
    )
    def test_list_model_public(self, route: str) -> None:
        """A 404 error should be raised for all private routes."""
        response = client.get(f"public/api/{route}")
        assert response.status_code == 404


class TestTreeOpenApiSchemas:
    """Each tree exposes its own fixed OpenAPI schema, independent of the client IP."""

    PRIVATE_PATHS = [
        "/list_model",
        "/add_model",
        "/update_model",
        "/add_source_type",
        "/update_source_type",
        "/add_data_category",
        "/update_data_category",
        "/add_location",
        "/update_location",
        "/add_layer",
        "/update_layer",
        "/clear_layer_field",
    ]

    PUBLIC_PATHS = [
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
    ]

    def test_public_tree_schema_excludes_private_routes(self) -> None:
        """The public tree schema contains public routes but no private ones."""
        paths = client.get("/public/api/openapi.json").json()["paths"]

        for path in self.PUBLIC_PATHS:
            assert path in paths
        for path in self.PRIVATE_PATHS:
            assert path not in paths

    def test_private_tree_schema_includes_private_routes(self) -> None:
        """The private tree schema contains both public and private routes."""
        paths = client.get("/private/api/openapi.json").json()["paths"]

        for path in self.PUBLIC_PATHS + self.PRIVATE_PATHS:
            assert path in paths
