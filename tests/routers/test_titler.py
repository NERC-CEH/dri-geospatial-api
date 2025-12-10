import base64
from pathlib import Path
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from starlette.responses import Response

from geospatial_api.main import app
from geospatial_api.routers.cached_titiler import TilerFactory

client = TestClient(app)


def check_image_response(response: Response) -> None:
    expected_image_bytes = (
        "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAADo0lEQVR4nO3cwVHDQBAAQYlcyD8soqDgAR8eQNmWfKeb7gj8mlrvrb1vEPD+"
        "9vox+jPM6GX0BwDGEQAIEwAI20d/ALiX7/WPMwFAmABAmABAmABAmABAmFcALsHG/xwmAAgTAAgTAAgTAAizBGQYi73xTAAQJgAQJgAQJgAQ"
        "JgAQJgAQJgAQJgAQJgAQJgAQJgAQJgAQJgAQJgAQJgAQ5v8AOJTf+F+LCQDCBADCBADCBADCBADCBADCBADCBADCBADCBADCnAJzFye/azAB"
        "QJgAQJgAQJgAQJgAQJhXAH6w3W8xAUCYAECYAECYAECYAECYAECYAECYAECYAECYAECYU+AoJ79smwkA0gQAwgQAwgQAwiwBAyz8+I0JAMIE"
        "AMIEAMIEAMIEAMIEAMIEAMIEAMIEAMIEAMKcAi/EyS+3MgFAmABAmABAmABAmABAmFeAydnscyYTAIQJAIQJAIQJAIQJAIQJAIQJAIQJAIQJ"
        "AIS5BJyIqz+ezQQAYQIAYQIAYQIAYQIAYV4BBrDtZxYmAAgTAAgTAAgTAAizBDyZhR8zMwFAmABAmABAmABAmABAmABAmABAmABAmABAmABA"
        "mFPggzj55YpMABAmABAmABAmABAmABDmFeAftvuszAQAYQIAYQIAYQIAYQIAYQIAYQIAYQIAYQIAYQIAYU6Bvzn5pcgEAGECAGECAGECAGHJ"
        "JaCFH3wxAUCYAECYAECYAECYAECYAECYAECYAECYAECYAEDY0qfATn7hbyYACBMACBMACBMACLvcEtBiD45jAoAwAYAwAYAwAYAwAYAwAYAw"
        "AYAwAYAwAYAwAYCwqU+Bnf3CuUwAECYAECYAECYAECYAEPb0VwCbfZiHCQDCBADCBADCBADCBADCBADCBADCBADCBADCBADCBADCBADCBADC"
        "BADCBADCDvk/AL/xh2syAUCYAECYAECYAECYAEDYza8ANv6wDhMAhAkAhAkAhAkAhAkAhAkAhAkAhAkAhAkAhO3b5roPqkwAECYAECYAECYA"
        "ECYAELZ7AYAuEwCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCE"
        "CQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCECQCEfQLi4lC3"
        "8Hu+JwAAAABJRU5ErkJggg=="
    )

    decoded_image_bytes = base64.b64encode(response.content).decode()

    if decoded_image_bytes != expected_image_bytes:
        raise ValueError("The returned image data does not match expected.")


class TestTitiler:
    def test_raster_from_s3_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Disable the cache to ensure that we are testing the core raster fetching logic
        monkeypatch.setenv("AIOCACHE_DISABLE", 1)

        response = client.get(
            "api/maps/tiles/WebMercatorQuad/16/32261/21043.png?url=S3://ukceh-fdri-staging-geospatial/raster/"
            "test_raster_3857_cog_rendered.tif"
        )

        assert response.status_code == 200
        check_image_response(response)

    def test_raster_from_file_url(self, monkeypatch: pytest.MonkeyPatch, data_dir: Path) -> None:
        # Disable the cache to ensure that we are testing the core raster fetching logic
        monkeypatch.setenv("AIOCACHE_DISABLE", 1)

        raster_path = data_dir.joinpath("test_raster_3857_cog_rendered.tif")
        response = client.get(f"api/maps/tiles/WebMercatorQuad/16/32261/21043.png?url=file:///{raster_path}")

        assert response.status_code == 200
        check_image_response(response)


class TestCachedTitiler:
    def test_cached_raster(self) -> None:
        """Check caching of raster tiles works correctly."""

        # Call the raster tile endpoint once initially to store the tile in the cache
        response_1 = client.get(
            "api/maps/tiles/WebMercatorQuad/16/32261/21043.png?url=S3://ukceh-fdri-staging-geospatial/raster/"
            "test_raster_3857_cog_rendered.tif"
        )

        assert response_1.status_code == 200
        check_image_response(response_1)

        with mock.patch.object(TilerFactory, "tile") as mock_tile:
            response_2 = client.get(
                "api/maps/tiles/WebMercatorQuad/16/32261/21043.png?url=S3://ukceh-fdri-staging-geospatial/raster/"
                "test_raster_3857_cog_rendered.tif"
            )
            # If caching has worked correctly, then the response should contain a valid image, but the tile function
            # from TilerFactor should not have been called
            mock_tile.assert_not_called()
            check_image_response(response_2)
