from typing import Annotated, Any, Generator

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session

from geospatial_api.config import setup_config
from geospatial_api.services.rds.auth import RDSLogin
from geospatial_api.services.rds.db import LayerRegistryInterface
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


# A database Session generator
SessionGenerator = RDSLogin.get_session_generator(config)


def get_db() -> Generator[Session, None, None]:
    db: Session = SessionGenerator()
    try:
        yield db
    finally:
        db.close()


@router.get("/available_data")
def get_available_data(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    layers = LayerRegistryInterface.get_db_entries(session=db)

    return JSONResponse([item.to_json_response() for item in layers])
