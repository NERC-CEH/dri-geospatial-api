from pathlib import Path
from urllib.parse import urlparse

import boto3
import boto3.session
from botocore.client import Config
from mypy_boto3_s3 import S3Client

from geospatial_api.config import LocalConfig, setup_config

boto3_config = Config(max_pool_connections=100)

config = setup_config()


def get_s3_client() -> S3Client:
    if isinstance(config, LocalConfig):
        session = boto3.session.Session(
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            region_name=config.AWS_DEFAULT_REGION,
        )
        endpoint_url = f"http://{config.endpoint_url}/"
        s3 = session.client("s3", endpoint_url=endpoint_url, config=boto3_config)
    else:
        s3 = boto3.client("s3", config=boto3_config)

    return s3


def get_file_path(url: str | Path, s3_client: S3Client) -> str:
    """
    Extract the file path from the provided url.

    It is assumed that the url is either a local path or an S3 url. The local path may have a file:// prefix that will
    need removing.

    Args:
        url: S3 url or local file path to be parsed
        s3_client: S3 Client to use to generate a presigned url to allow download of the S3 data.

    Returns:
        Parsed local file path or presigned s3 url.

    """
    # If a pathlib.Path object has been passed in then the file path should already be valid and can be returned
    # directly
    if isinstance(url, Path):
        check_path_exists(url)
        return str(url)

    url_parts = urlparse(url)
    file_path = url_parts.path.replace("//", "/")

    if url_parts.scheme.lower() == "s3":
        key = file_path.lstrip("/")
        file_path = s3_client.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": url_parts.netloc, "Key": key}
        )
        return file_path

    if url_parts.scheme == "file":
        check_path_exists(file_path)
        return file_path


def check_path_exists(path: str | Path) -> None:
    """
    Check a local file path exists

    Args:
        path: Pathlib.path or str representation of the file path.

    Raises:
        FileExistsError: The path does not exist.

    """
    path = Path(path)
    if not path.exists():
        raise FileExistsError(f"The provided path does not exist: {str(path)}")
