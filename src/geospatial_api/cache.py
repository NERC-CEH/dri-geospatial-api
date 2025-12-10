"""Logic for caching Titiler taken from https://developmentseed.org/titiler/examples/code/tiler_with_cache/."""

import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Callable

import aiocache
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .settings import cache_setting


class CachedABC(ABC, aiocache.cached):
    """Abstract base class for caching endpoint data"""

    async def get_from_cache(self, key: str) -> str | Response | None:
        try:
            value = await self.cache.get(key)
            if isinstance(value, Response):
                value.headers["X-Cache"] = "HIT"
            return value
        except Exception:
            aiocache.logger.exception("Couldn't retrieve %s, unexpected error", key)

    @abstractmethod
    async def read_cache(self, key: str) -> Response:
        """Read data from the cache.

        Args:
            key: key indexing the cached data to be returned.

        Returns:
            Response constructed from the cached data.

        """
        pass

    @abstractmethod
    async def write_cache(self, key: str, result: Response) -> None:
        """
        Write data to the cache.

        Args:
            key: Key to use as an index for the data to be written within the cache.
            result: Response data to write to the cache.

        """
        pass

    async def decorator(
        self,
        f: Callable,
        *args,
        **kwargs,
    ) -> Response:
        """
        The main decorator function

        If data is available from the cache for the underlying router function, then it will be returned. Otherwise
        the router function will be called and the response written to the cache before being returned.

        Args:
            f: Router function used to generate the data to be returned as a Response object.mro

        Returns:
            Response read from the cache, or from the provided router function.

        """
        key = self.get_cache_key(f, args, kwargs)

        result = await self.read_cache(key)
        if result is not None:
            return result

        result = await run_in_threadpool(f, *args, **kwargs)

        # Write any new tile data to cache
        await self.write_cache(key, result)

        return result


class CachedTiles(CachedABC):
    """Custom Cached Decorator for Titiler tile route(s)."""

    async def read_cache(self, key: str) -> Response | None:
        """Read data from the cache.

        To construct the returned response object, the image bytes data needs to be extracted from the stored json,
        and decoded it from its bytes64 encoding. The headers can be used directly once the json string has been
        converted back to a dictionary.

        Args:
            key: key indexing the cached data to be returned.

        Returns:
            Response constructed from the cached data.

        """
        value = await self.get_from_cache(key)
        if value is None:
            return

        # Extract the tile image and headers from the stored data
        result_data = json.loads(value)
        image_bytes = base64.b64decode(result_data["body"].encode())
        response = Response(image_bytes, headers=result_data["headers"])
        return response

    async def write_cache(self, key: str, result: Response) -> None:
        """
        Write data to the cache.

        In order to store the tiled image, the image data is converted to a string representation of dictionary
        containing the following data
        {
                "body": image byte data encoded as a bytes64 string,
                "headers": {
                    "content-bbox": "-310028.5867247395,7169181.756923294,-309417.0904984586,7169793.2531495765",
                    "content-crs": "<http://www.opengis.net/def/crs/EPSG/0/3857>",
                    "content-length": "988",
                    "content-type": "image/png"
                    }
            }

        Args:
            key: Key to use as an index for the data to be written within the cache.
            result: Response data to write to the cache.

        """
        image_bytes = base64.b64encode(result.body)
        data_to_cache = json.dumps(
            {
                "body": image_bytes.decode(),
                "headers": {key.decode(): value.decode() for (key, value) in result.headers.raw},
            }
        )
        await self.set_in_cache(key, data_to_cache)


def setup_cache() -> None:
    """Setup aiocache."""
    config: dict[str, Any] = {
        "cache": "aiocache.SimpleMemoryCache",
        "serializer": {"class": "aiocache.serializers.PickleSerializer"},
    }
    if cache_setting.ttl is not None:
        config["ttl"] = cache_setting.ttl
