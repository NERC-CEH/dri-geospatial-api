from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from mypy_boto3_s3 import S3Client

from geospatial_api.config import setup_config
from geospatial_api.utils import get_s3_client

router = APIRouter()

config = setup_config()
s3 = get_s3_client()

EXT_MAPPING = {"tif": "raster", "geojson": "vector"}


@router.get("/available_data")
def available_data(s3_client: S3Client = Depends(lambda: s3)) -> dict[str, Any]:
    data = []
    items = s3_client.list_objects_v2(Bucket=config.geospatial_data_bucket)

    for idx, item in enumerate(items.get("Contents", [])):
        key = item["Key"]
        if any([key.endswith(suffix) for suffix in EXT_MAPPING.keys()]):
            name, ext = key.split("/")[-1].split(".")
            data.append(
                {
                    "id": idx,
                    "name": name,
                    "data_type": EXT_MAPPING.get(ext, "unknown"),
                    "s3_url": f"S3://{config.geospatial_data_bucket}/{item['Key']}",
                    "geojson": None,
                }
            )
    return JSONResponse(data)
