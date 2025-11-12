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


def get_file_path(url: str, s3_client: S3Client) -> str:
    url_parts = urlparse(url)
    if url_parts.scheme.lower() == "s3":
        key = url_parts.path.replace("//", "/").lstrip("/")
        file_path = s3_client.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": url_parts.netloc, "Key": key}
        )
    elif url_parts.scheme == "file":
        file_path = url_parts.path

    return file_path
