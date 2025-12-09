from typing import Optional

from pydantic_settings import BaseSettings


class CacheSettings(BaseSettings):
    """Cache settings"""

    endpoint: Optional[str] = None
    ttl: int = 3600
    namespace: str = ""

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CACHE_"


cache_setting = CacheSettings()
