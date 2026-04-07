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
        "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAB60lEQVR4nO3ZwSpEYRgG4G+mU2NhlBmUFKXJRlIWsrBQdvYsrWwtXIWycgGy"
        "dAlspsZWKclGDAuUKYthIQw5ruGok46e5wLe3s3/9fX9EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAA/Bulvy4A/N7U1Fra1xuI18ZC3DQ3Mr/nch6lgPxNzO+kvbGlKI8uRlIbi4/WSpo1I8mjGJC/ke3nSEdL8bxX"
        "ieXJuzhvzUXEYaYMAwAKauvoMYbmh2Nw9To6Fx/RfnnPnGEAQEHVZxaiWhuP5k4jqvEVpdn9zBluAFBQt51udN7SOPi8j932SVTrZ5kzbABQ"
        "UJXp/rhMrqJ7ehzJ91Osbz741QMAAAAAAAAAAAAAAAAAAAAAAACAgvgBF1g1Lx3BssMAAAAASUVORK5CYII="
    )

    decoded_image_bytes = base64.b64encode(response.content).decode()

    if decoded_image_bytes != expected_image_bytes:
        raise ValueError("The returned image data does not match expected.")


class TestTitiler:
    def test_raster_from_s3_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Disable the cache to ensure that we are testing the core raster fetching logic
        monkeypatch.setenv("AIOCACHE_DISABLE", 1)

        response = client.get(
            "api/maps/tiles/WebMercatorQuad/15/16072/10282.png?url=s3://ukceh-fdri-staging-geospatial/project=fdri"
            "/area_type=catchment/area_name=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/"
            "clipped_tweed_dsm_3857_colourised_cog.tif"
        )

        assert response.status_code == 200
        check_image_response(response)

    def test_raster_from_file_url(self, monkeypatch: pytest.MonkeyPatch, data_dir: Path) -> None:
        # Disable the cache to ensure that we are testing the core raster fetching logic
        monkeypatch.setenv("AIOCACHE_DISABLE", 1)

        raster_path = data_dir.joinpath("clipped_tweed_dsm_3857_colourised_cog.tif")
        response = client.get(f"api/maps/tiles/WebMercatorQuad/15/16072/10282.png?url=file:///{raster_path}")

        assert response.status_code == 200
        check_image_response(response)


class TestCachedTitiler:
    def test_cached_raster(self) -> None:
        """Check caching of raster tiles works correctly."""

        # Call the raster tile endpoint once initially to store the tile in the cache
        response_1 = client.get(
            "api/maps/tiles/WebMercatorQuad/15/16072/10282.png?url=s3://ukceh-fdri-staging-geospatial/project=fdri"
            "/area_type=catchment/area_name=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/"
            "clipped_tweed_dsm_3857_colourised_cog.tif"
        )

        assert response_1.status_code == 200
        check_image_response(response_1)

        with mock.patch.object(TilerFactory, "tile") as mock_tile:
            response_2 = client.get(
                "api/maps/tiles/WebMercatorQuad/15/16072/10282.png?url=s3://ukceh-fdri-staging-geospatial/project=fdri"
                "/area_type=catchment/area_name=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/"
                "clipped_tweed_dsm_3857_colourised_cog.tif"
            )
            # If caching has worked correctly, then the response should contain a valid image, but the tile function
            # from TilerFactor should not have been called
            mock_tile.assert_not_called()
            check_image_response(response_2)
