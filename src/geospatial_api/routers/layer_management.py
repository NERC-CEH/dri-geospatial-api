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
from geospatial_api.services.rds.db import (
    DataCategoryModelInterface,
    IDModelInterface,
    LayerRegistryInterface,
    LocationModelInterface,
)
from geospatial_api.utils.utils import get_db, get_s3_client

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
    "data_category_group": ModelMap(
        db_model=db_models.DataCategoryGroup, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "data_category": ModelMap(
        db_model=db_models.DataCategory,
        model_interface=DataCategoryModelInterface,
        pydantic_model=py_models.DataCategory,
    ),
    "processing_level": ModelMap(
        db_model=db_models.ProcessingLevel, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "location_type": ModelMap(
        db_model=db_models.LocationType, model_interface=IDModelInterface, pydantic_model=py_models.IDModel
    ),
    "location": ModelMap(
        db_model=db_models.Location, model_interface=LocationModelInterface, pydantic_model=py_models.Location
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


@router.post("/add_data_category")
def add_data_category(
    db: Annotated[Session, Depends(get_db)],
    name: str,
    object_key: str,
    category_group_key: str,
) -> JSONResponse:
    new_db_item = DataCategoryModelInterface.add_new_entry(
        session=db,
        name=name,
        object_key=object_key,
        data_category_group_key=category_group_key,
    )

    return JSONResponse(status_code=200, content=f"Successfully created new data category {new_db_item.name}")


@router.post("/add_location")
def add_location(
    db: Annotated[Session, Depends(get_db)],
    name: str,
    object_key: str,
    location_type_key: str,
    boundary: UploadFile,
) -> JSONResponse:
    new_db_item = LocationModelInterface.add_new_entry(
        session=db,
        name=name,
        object_key=object_key,
        location_type_key=location_type_key,
        boundary=geojson.load(boundary.file),
    )

    return JSONResponse(status_code=200, content=f"Successfully created new location {new_db_item.name}")


@router.post("/add_layer")
async def add_layer(
    db: Annotated[Session, Depends(get_db)],
    name: str,
    project: str,
    source_type: str,
    data_format: str,
    data_category: str,
    processing_level: str,
    location: str,
    description: str | None = None,
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    colour_source_id: str | None = None,
    colour_source_file: UploadFile | None = None,
    raw_source_id: str | None = None,
    raw_source_file: UploadFile | None = None,
    legend: UploadFile | None = None,
    boundary: UploadFile | None = None,
    field_metadata: UploadFile | None = None,
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

    # Ensure the provided field metadata file is a json
    if field_metadata and not field_metadata.filename.lower().endswith(".json"):
        raise HTTPException("Field metadata must be provided as a .json file.")

    # Ensure the provided boundary file is a geojson
    if boundary and not boundary.filename.lower().endswith(".geojson"):
        raise HTTPException("The boundary must be provided as a .geojson file.")

    # Ensure either a single date, or a combination of start date and end date have been provided
    if (
        (not date and not start_date and not end_date)
        or (date and (start_date or end_date))
        or (end_date and not date and not start_date)
    ):
        raise HTTPException(
            "Either a single date or a start and end date combination need to be provided. "
            "If the dataset is ongoing, leave the end date blank"
        )

    new_layer = LayerRegistryInterface.add_new_layer(
        session=db,
        name=name,
        description=description,
        project_key=project,
        date=datetime.strptime(date, "%Y-%m-%d") if date else None,
        start_date=datetime.strptime(start_date, "%Y-%m-%d") if start_date else None,
        end_date=datetime.strptime(end_date, "%Y-%m-%d") if end_date else None,
        source_type_key=source_type,
        data_format_key=data_format,
        data_category_key=data_category,
        processing_level_key=processing_level,
        area_name_key=location,
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
