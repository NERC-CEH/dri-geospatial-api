from typing import Annotated, Any

import geojson
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from geospatial_api.config import setup_config
from geospatial_api.services.rds.db import LayerRegistryInterface, LocationModelInterface
from geospatial_api.utils.utils import get_db, get_os_api_key, get_s3_client

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

OS_API_KEY = get_os_api_key()


def serves_private_view(request: Request) -> bool:
    """Whether the current route tree serves the full (private) view.

    Returns:
        ``True`` when the request is served by the private tree, else ``False``.
    """
    return request.app.state.serves_private_view


@router.get("/available_data")
def get_available_data(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    layers = LayerRegistryInterface.get_db_entries(session=db)

    return JSONResponse([item.to_json_response() for item in layers])


@router.get("/location_boundary")
def get_location_boundary(db: Annotated[Session, Depends(get_db)], location_id: int) -> dict[str, Any]:
    location = LocationModelInterface.get_single_location(session=db, location_id=location_id)
    geojson_feature = geojson.Feature(geometry=location.boundary)
    return geojson.FeatureCollection([geojson_feature])


@router.get("/basemap/{map_name}/{z}/{x}/{y}")
async def get_basemap(
    map_name: str,
    x: int,
    y: int,
    z: int,
    request: Request,
    response: Response,
) -> Response:
    """
    Get the corresponding OS basemap tile based on the map name and tile coordinates.

    Args:
        map_name: Name of the OS map
        x: X tile ref
        y: Y tile ref
        z: Z tile ref
        request: Original Request object
        response: Original Response object

    Raises:
        HTTPException: Incorrect header origin
        HTTPException: No API Key

    Returns:
        OS map tile as a Response object

    """
    for host_url in config.host_urls:
        if not request.headers["origin"].startswith(host_url):
            raise HTTPException(status_code=403)

    if not OS_API_KEY:
        raise HTTPException(status_code=500, detail="Invalid api key")

    url = f"https://api.os.uk/maps/raster/v1/zxy/{map_name}/{z}/{x}/{y}.png?key={OS_API_KEY}"

    async with httpx.AsyncClient() as client:
        proxy = await client.get(url)

    response.body = proxy.content
    response.status_code = proxy.status_code
    return response
