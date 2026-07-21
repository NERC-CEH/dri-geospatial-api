from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from geospatial_api.main import app
from geospatial_api.models import Layer, SourceType
from geospatial_api.utils.vector_https_utils import fetch_data, fetch_vector_data_from_https
from httpx import HTTPError, Request, Response

client = TestClient(app)


class TestFetchData:
    def test_no_response(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(status_code=504, request=mock_request)
            mock_get.return_value = mock_response

            with pytest.raises(HTTPError):
                fetch_data("http://test_url.com")

    def test_invalid_json_response(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(status_code=200, json=None, request=mock_request)
            mock_get.return_value = mock_response

            with pytest.raises(ValueError):
                fetch_data("http://test_url.com")


class TestFetchVectorDataFromHTTPS:
    def test_invalid_source_type(self) -> None:
        with (
            patch("requests.Session.get") as mock_get,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json={}, request=mock_request)
            mock_get.return_value = mock_response

            with pytest.raises(ValueError, match="The source type of the layer is not supported"):
                fetch_vector_data_from_https(
                    url="http://test_url.com",
                    layer=Layer.model_construct(
                        source_type=SourceType.model_construct(object_key="random_source_type")
                    ),
                )
