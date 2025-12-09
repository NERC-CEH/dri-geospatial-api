"""Logic for caching Titiler taken from https://developmentseed.org/titiler/examples/code/tiler_with_cache/."""

import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Dict

import aiocache
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .settings import cache_setting


class CachedABC(ABC, aiocache.cached):
    async def get_from_cache(self, key: str) -> str | Response:
        try:
            value = await self.cache.get(key)
            if isinstance(value, Response):
                value.headers["X-Cache"] = "HIT"
            return value
        except Exception:
            aiocache.logger.exception("Couldn't retrieve %s, unexpected error", key)

    @abstractmethod
    async def read_cache(self, key: str) -> Response:
        pass

    @abstractmethod
    async def write_cache(self, key: str, result: Response) -> None:
        pass

    async def decorator(
        self,
        f: callable,
        *args,
        **kwargs,
    ) -> Response:
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

    async def read_cache(self, key: str) -> Response:
        value = await self.get_from_cache(key)
        if value is None:
            return

        # Extract the tile image and headers from the stored data
        result_data = json.loads(value)
        image_bytes = base64.b64decode(result_data["body"].encode())
        response = Response(image_bytes, headers=result_data["headers"])
        return response

    async def write_cache(self, key: str, result: Response) -> None:
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
    config: Dict[str, Any] = {
        "cache": "aiocache.SimpleMemoryCache",
        "serializer": {"class": "aiocache.serializers.PickleSerializer"},
    }
    if cache_setting.ttl is not None:
        config["ttl"] = cache_setting.ttl
