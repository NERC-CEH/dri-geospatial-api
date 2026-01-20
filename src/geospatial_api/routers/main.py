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

# Temporary mapping of layer names to map centres to be used until a database is available to provide the information
DEFAULT_MAP_CENTRE = (54.238, -1.926)  # Roughly the centre of the UK
LAYER_CENTRES = {
    "heathstane": (55.520017, -3.392571),
    "tweedsmuir": (55.515457, -3.414769),
    "gblcm": (54.238, -1.926),
    "severn": (52.45808, -3.59893),
    "chess": (51.71587, -0.58875),
    "test": (54.008128, -2.774925),
}


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
                    "map_centre": get_map_centre(name),
                    "colourmap_name": "terrain" if "greyscale" in name.lower() else None,
                }
            )
    return JSONResponse(data)


def get_map_centre(layer_name: str) -> tuple[float, float]:
    for name_fragment, layer_centre in LAYER_CENTRES.items():
        if name_fragment.lower() in layer_name.lower():
            return layer_centre

    return DEFAULT_MAP_CENTRE
