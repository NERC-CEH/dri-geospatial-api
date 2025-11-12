import os
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_PATH = Path(__file__).parent / "__assets__" / "config.env"


class BaseConfig(BaseSettings):
    """Base config model.

    Attributes:
        api_version: The version of the api
        AWS_DEFAULT_REGION: The required AWS region
    """

    api_version: str
    AWS_DEFAULT_REGION: str
    api_environment: str

    title: str
    description: str
    contact_name: str
    contact_url: str
    geospatial_data_bucket: str
    metadata_url: str

    @field_validator("api_environment")
    def check_api_environment(cls, value: str) -> str:
        """Validate the api_environment variable."""
        if value not in ["staging", "production"]:
            raise ValueError(f"api_environment parameter must be one of ['staging', 'production'], not '{value}'")

        return value


class LocalConfig(BaseConfig):
    """Local config model.

    When running locally, config parameters are loaded from a .env file as they do not exist
    as environment variables.

    Attributes:
        AWS_ACCESS_KEY_ID: AWS access key id
        AWS_SECRET_ACCESS_KEY: AWS secret access key
        api_environment: What environment is the api running
        endpoint_url: URL to the AWS endpoint
    """

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_NO_SIGN_REQUEST: str
    endpoint_url: str

    api_environment: str = "local"
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH)

    @field_validator("api_environment")
    def check_api_environment(cls, value: str) -> str:
        return value


def setup_config() -> Any:
    # Setup API run environment
    if "api_environment" in os.environ and os.environ["api_environment"] in ["staging", "production"]:
        # Type checking is ignored for BaseConfig as the inputs are taken from environment variables, which causes
        # pyright to error
        return BaseConfig()  # type: ignore

    # # Type checking is ignored for BaseConfig as the inputs are taken from environment variables, which causes
    # pyright to error
    return LocalConfig()  # type: ignore
