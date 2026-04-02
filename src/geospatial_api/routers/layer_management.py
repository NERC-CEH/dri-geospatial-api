import json
from collections import namedtuple
from datetime import datetime
from typing import Annotated

import geojson
from dri_database_models import geospatial as db_models
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from mypy_boto3_s3 import S3Client
from sqlalchemy.orm import Session

from geospatial_api import models as py_models
from geospatial_api.config import setup_config
from geospatial_api.services.rds.db import AreaNameModelInterface, IDModelInterface, LayerRegistryInterface
from geospatial_api.utils import get_db, get_s3_client

router = APIRouter(tags=["Layer Management"])
s3 = get_s3_client()
config = setup_config()

ModelMap = namedtuple("ModelMap", ["db_model", "model_interface", "pydantic_model"])

MODEL_MAPPING = {
    "project": ModelMap(db_model=db_models.Project, model_interface=IDModelInterface, pydantic_model=py_models.IDModel),
    "source_type": ModelMap(
        db_model=db_models.SourceType, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "data_format": ModelMap(
        db_model=db_models.DataFormat, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "data_category": ModelMap(
        db_model=db_models.DataCategory, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "processing_level": ModelMap(
        db_model=db_models.ProcessingLevel, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "area_type": ModelMap(
        db_model=db_models.AreaType, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "area_name": ModelMap(
        db_model=db_models.AreaName, model_interface=AreaNameModelInterface, pydantic_model=py_models.AreaName
    ),
}


@router.get("/list_model")
def get_model(model_name: str, db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    model_mapping = MODEL_MAPPING.get(model_name)
    if not model_mapping:
        raise HTTPException(f"The model {model_name} is not supported")

    model_items = model_mapping.model_interface.get_db_entries(session=db, db_model=model_mapping.db_model)

    return JSONResponse([item.to_json_response() for item in model_items])


@router.post("/add_model")
def add_model(db: Annotated[Session, Depends(get_db)], model_name: str, name: str, object_key: str) -> JSONResponse:
    model_mapping = MODEL_MAPPING.get(model_name)
    if not model_mapping:
        raise HTTPException(f"The model {model_name} is not supported")

    new_db_item = model_mapping.model_interface.add_model_entry(
        session=db, db_model=model_mapping.db_model, name=name, object_key=object_key
    )
    new_model = model_mapping.model_interface.convert_to_pydantic_model(new_db_item)

    return JSONResponse(status_code=200, content=f"Successfully created {model_name} {new_model.name}")


@router.post("/add_area_name")
def add_area_name(
    db: Annotated[Session, Depends(get_db)], name: str, object_key: str, area_type_key: str
) -> JSONResponse:
    new_db_item = AreaNameModelInterface.add_new_entry(
        session=db, name=name, object_key=object_key, area_type_key=area_type_key
    )

    return JSONResponse(status_code=200, content=f"Successfully created new area name {new_db_item.name}")


@router.post("/add_layer")
async def add_layer(
    db: Annotated[Session, Depends(get_db)],
    name: str,
    project: str,
    date: str,
    source_type: str,
    data_format: str,
    data_category: str,
    processing_level: str,
    area_name: str,
    colour_source_id: str | None = None,
    colour_source_file: UploadFile | None = None,
    raw_source_id: str | None = None,
    raw_source_file: UploadFile | None = None,
    legend: UploadFile | None = None,
    boundary: UploadFile | None = None,
    s3_client: S3Client = Depends(lambda: s3),
) -> JSONResponse:
    if not colour_source_id and not colour_source_file and not raw_source_id and not raw_source_file:
        raise HTTPException(
            "Either the source_id or the source_file should be provided for one or more of the raw or colour source "
            "options"
        )

    # Ensure the provided legend file is a json
    if legend and not legend.filename.lower().endswith(".json"):
        raise HTTPException("The legend must be provided as a .json file.")

    # Ensure the provided boundary file is a geojson
    if boundary and not boundary.filename.lower().endswith(".geojson"):
        raise HTTPException("The boundary must be provided as a .geojson file.")

    new_layer = LayerRegistryInterface.add_new_layer(
        session=db,
        name=name,
        project_key=project,
        date=datetime.strptime(date, "%Y-%m-%d"),
        source_type_key=source_type,
        data_format_key=data_format,
        data_category_key=data_category,
        processing_level_key=processing_level,
        area_name_key=area_name,
        colour_source_id=colour_source_file.filename if colour_source_file else colour_source_id,
        raw_source_id=raw_source_file.filename if raw_source_file else raw_source_id,
        legend=json.load(legend.file) if legend else None,
        boundary=geojson.load(boundary.file) if boundary else None,
    )

    layer = LayerRegistryInterface.convert_layer_to_pydantic_model(session=db, db_layer=new_layer)

    # If the source type is S3 and a source_file has been provided, upload the data to S3 in the appropriate bucket
    if colour_source_file:
        destination_key = layer.get_source_url(source_id=colour_source_file.filename).replace(
            f"s3://{config.geospatial_data_bucket}/", ""
        )
        content = await colour_source_file.read()
        s3_client.put_object(Bucket=config.geospatial_data_bucket, Key=destination_key, Body=content)

    if raw_source_file:
        destination_key = layer.get_source_url(source_id=raw_source_file.filename).replace(
            f"s3://{config.geospatial_data_bucket}/", ""
        )
        content = await raw_source_file.read()
        s3_client.put_object(Bucket=config.geospatial_data_bucket, Key=destination_key, Body=content)

    return JSONResponse(status_code=200, content=f"Successfully created layer {layer.name}")
