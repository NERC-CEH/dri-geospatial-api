import logging
from functools import lru_cache

from fastapi import Depends
from mypy_boto3_s3 import S3Client
from titiler.extensions import cogValidateExtension, cogViewerExtension, wmsExtension

from geospatial_api.routers.cached_titiler import TilerFactory
from geospatial_api.utils import get_file_path, get_s3_client

logger = logging.getLogger(__name__)

s3 = get_s3_client()


# Custom Path dependency which will sign s3 url
@lru_cache
def DatasetPathParams(url: str, s3_client: S3Client = Depends(lambda: s3)) -> str:
    """Create dataset path from args"""
    # Use your provider library to sign the URL
    file_path = get_file_path(url, s3_client)
    return file_path


# Create a TilerFactory for Cloud-Optimized GeoTIFFs
cog = TilerFactory(
    path_dependency=DatasetPathParams,
    router_prefix="/maps",
    extensions=[wmsExtension(), cogValidateExtension(), cogViewerExtension()],
)
router = cog.router
