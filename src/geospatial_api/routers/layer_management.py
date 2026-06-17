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
    SourceTypeModelInterface,
)
from geospatial_api.utils.ip_whitelisting import require_whitelisted_ip_address
from geospatial_api.utils.utils import get_db, get_s3_client

private_router = APIRouter(tags=["Layer Management"], dependencies=[Depends(require_whitelisted_ip_address)])

s3 = get_s3_client()
config = setup_config()

ModelMap = namedtuple("ModelMap", ["db_model", "model_interface", "pydantic_model"])

MODEL_MAPPING = {
    "project": ModelMap(db_model=db_models.Project, model_interface=IDModelInterface, pydantic_model=py_models.IDModel),
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
    "source_type": ModelMap(
        db_model=db_models.SourceType, model_interface=SourceTypeModelInterface, pydantic_model=py_models.IDModel
    ),
}


@private_router.get("/list_model")
def get_model(model_name: str, db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    model_mapping = MODEL_MAPPING.get(model_name)
    if not model_mapping:
        raise HTTPException(f"The model {model_name} is not supported")

    model_items = model_mapping.model_interface.get_db_entries(session=db, db_model=model_mapping.db_model)

    return JSONResponse([item.to_json_response() for item in model_items])


@private_router.post("/add_model")
def add_model(db: Annotated[Session, Depends(get_db)], model_name: str, name: str, object_key: str) -> JSONResponse:
    model_mapping = MODEL_MAPPING.get(model_name)
    if not model_mapping:
        raise HTTPException(f"The model {model_name} is not supported")

    new_db_item = model_mapping.model_interface.add_model_entry(
        session=db, db_model=model_mapping.db_model, name=name, object_key=object_key
    )
    new_model = model_mapping.model_interface.convert_to_pydantic_model(new_db_item)

    return JSONResponse(status_code=200, content=f"Successfully created {model_name} {new_model.name}")


@private_router.post("/update_model")
def update_model(
    db: Annotated[Session, Depends(get_db)],
    model_name: str,
    model_id: int,
    name: str | None = None,
    object_key: str | None = None,
) -> JSONResponse:
    model_mapping = MODEL_MAPPING.get(model_name)
    if not model_mapping:
        raise HTTPException(f"The model {model_name} is not supported")

    new_db_item = model_mapping.model_interface.update_model_entry(
        session=db, db_model=model_mapping.db_model, model_id=model_id, name=name, object_key=object_key
    )
    updated_model_item = model_mapping.model_interface.convert_to_pydantic_model(new_db_item)

    return JSONResponse(status_code=200, content=updated_model_item.to_json_response())


@private_router.post("/add_source_type")
def add_source_type(
    db: Annotated[Session, Depends(get_db)],
    name: str,
    object_key: str,
    category_group_key: str,
) -> JSONResponse:
    new_db_item = SourceTypeModelInterface.add_new_entry(
        session=db,
        name=name,
        object_key=object_key,
        data_category_group_key=category_group_key,
    )

    return JSONResponse(status_code=200, content=f"Successfully created new source type {new_db_item.name}")


@private_router.post("/update_source_type")
def update_source_type(
    db: Annotated[Session, Depends(get_db)],
    model_id: int,
    name: str | None = None,
    object_key: str | None = None,
    base_url: str | None = None,
) -> JSONResponse:
    updated_db_item = SourceTypeModelInterface.update_entry(
        session=db,
        model_id=model_id,
        name=name,
        object_key=object_key,
        base_url=base_url,
    )

    source_type = SourceTypeModelInterface.convert_db_item_to_pydantic_model(session=db, db_item=updated_db_item)

    return JSONResponse(status_code=200, content=source_type.to_json_response())


@private_router.post("/add_data_category")
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


@private_router.post("/update_data_category")
def update_data_category(
    db: Annotated[Session, Depends(get_db)],
    model_id: int,
    name: str | None = None,
    object_key: str | None = None,
    category_group_key: str | None = None,
) -> JSONResponse:
    updated_db_item = DataCategoryModelInterface.update_entry(
        session=db,
        model_id=model_id,
        name=name,
        object_key=object_key,
        data_category_group_key=category_group_key,
    )

    data_category = DataCategoryModelInterface.convert_db_item_to_pydantic_model(session=db, db_item=updated_db_item)

    return JSONResponse(status_code=200, content=data_category.to_json_response())


@private_router.post("/add_location")
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


@private_router.post("/update_location")
def update_location(
    db: Annotated[Session, Depends(get_db)],
    model_id: int,
    name: str | None = None,
    object_key: str | None = None,
    location_type_key: str | None = None,
    boundary: UploadFile | None = None,
) -> JSONResponse:
    if boundary is not None:
        boundary = geojson.load(boundary.file)

    updated_db_item = LocationModelInterface.update_entry(
        session=db,
        model_id=model_id,
        name=name,
        object_key=object_key,
        location_type_key=location_type_key,
        boundary=boundary,
    )

    location = LocationModelInterface.convert_db_item_to_pydantic_model(session=db, db_item=updated_db_item)

    return JSONResponse(status_code=200, content=location.to_json_response())


@private_router.post("/add_layer")
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
        location_key=location,
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


@private_router.post("/update_layer")
async def update_layer(
    db: Annotated[Session, Depends(get_db)],
    model_id: str,
    name: str | None = None,
    project: str | None = None,
    source_type: str | None = None,
    data_format: str | None = None,
    data_category: str | None = None,
    processing_level: str | None = None,
    location: str | None = None,
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

    new_layer = LayerRegistryInterface.update_layer(
        session=db,
        model_id=model_id,
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
        location_key=location,
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
