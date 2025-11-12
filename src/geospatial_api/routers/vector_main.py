from typing import Any
from urllib.parse import urlparse

import geojson
from fastapi import APIRouter, Depends
from mypy_boto3_s3 import S3Client

from geospatial_api.utils import get_file_path, get_s3_client

router = APIRouter(tags=["Vector Data"])
s3 = get_s3_client()


@router.get("/vector")
def read_index(url: str, s3_client: S3Client = Depends(lambda: s3)) -> dict[str, Any]:
    url_parts = urlparse(url)
    print(f"Attempting to load vector from: {url}")
    if url_parts.scheme.lower() == "s3":
        response = s3_client.get_object(Bucket=url_parts.netloc, Key=url_parts.path.lstrip("/"))
        geojson_data = geojson.load(response["Body"])
    else:
        # Sometimes urlparse doesn't remove the file://// prefix correctly, therefore ensure only single / are present
        file_path = get_file_path(url, s3_client).replace("//", "/")
        with open(file_path) as geojson_file:
            geojson_data = geojson.load(geojson_file)

    return geojson_data
