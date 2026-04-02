import logging
from typing import Any

import shapely
from dri_database_models import geospatial as db_models
from geoalchemy2.shape import to_shape
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from geospatial_api import models
from geospatial_api.config import setup_config

logger = logging.getLogger(__name__)

config = setup_config()


def add_db_item(session: Session, db_item: object) -> None:
    try:
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
    except SQLAlchemyError as e:
        session.rollback()
        logger.error("Failed to write data to database.")
        logger.exception(e)
        raise
    finally:
        session.close()
        return db_item


def get_db_object_by_key(session: Session, db_model: object, object_key: str) -> object:
    db_object = session.query(db_model).filter_by(object_key=object_key).first()
    if not db_object:
        raise ValueError(
            f"Could not fetch model instance `{str(db_model)} for key: {object_key}. Object may not exist."
        )

    return db_object


class LayerRegistryInterface:
    @staticmethod
    def get_db_entries(session: Session) -> list[models.Layer]:
        layers = []
        query = session.query(db_models.Layer)
        for item in query:
            layers.append(LayerRegistryInterface.convert_layer_to_pydantic_model(session=session, db_layer=item))

        return layers

    @staticmethod
    def get_instance(
        session: Session,
        model_id: int,
        model_class: object,
        pydantic_model: object,
    ) -> object:
        model_instance = session.get(model_class, model_id)

        model_dict = {}
        for field in pydantic_model.model_fields.keys():
            model_dict[field] = getattr(model_instance, field)

        return pydantic_model(**model_dict)

    @staticmethod
    def get_area_name_instance(session: Session, area_name_id: int) -> models.AreaName:
        area_name = session.get(db_models.AreaName, area_name_id)
        area_type = LayerRegistryInterface.get_instance(
            session=session,
            model_id=area_name.area_type,
            model_class=db_models.AreaType,
            pydantic_model=models.IDModel,
        )

        return models.AreaName(
            id=area_name.id,
            last_updated=area_name.last_updated,
            name=area_name.name,
            object_key=area_name.object_key,
            area_type=area_type,
        )

    @staticmethod
    def add_new_layer(
        session: Session,
        name: str,
        project_key: str,
        date: str,
        source_type_key: str,
        data_format_key: str,
        data_category_key: str,
        processing_level_key: str,
        area_name_key: str,
        source_id: str | None = None,
        legend: dict[str, Any] | None = None,
        boundary: dict[str, Any] | None = None,
    ) -> db_models.Layer:
        # Get the instance of dependent models, matching on object_key values
        project = get_db_object_by_key(session=session, db_model=db_models.Project, object_key=project_key)
        source_type = get_db_object_by_key(session=session, db_model=db_models.SourceType, object_key=source_type_key)
        data_format = get_db_object_by_key(session=session, db_model=db_models.DataFormat, object_key=data_format_key)
        data_category = get_db_object_by_key(
            session=session, db_model=db_models.DataCategory, object_key=data_category_key
        )
        processing_level = get_db_object_by_key(
            session=session, db_model=db_models.ProcessingLevel, object_key=processing_level_key
        )
        area_name = get_db_object_by_key(session=session, db_model=db_models.AreaName, object_key=area_name_key)
        boundary_geom = shapely.geometry.shape(boundary.features[0])
        bbox = shapely.box(*boundary_geom.bounds)
        new_layer = add_db_item(
            session=session,
            db_item=db_models.Layer(
                name=name,
                project=project.id,
                date=date,
                source_type=source_type.id,
                data_format=data_format.id,
                data_category=data_category.id,
                processing_level=processing_level.id,
                area_name=area_name.id,
                source_id=source_id,
                legend=legend,
                boundary=boundary_geom.wkt,
                bbox=bbox.wkt,
            ),
        )

        return new_layer

    @staticmethod
    def convert_layer_to_pydantic_model(session: Session, db_layer: db_models.Layer) -> models.Layer:
        bbox = to_shape(db_layer.bbox)

        source_type = LayerRegistryInterface.get_instance(
            session=session,
            model_id=db_layer.source_type,
            model_class=db_models.SourceType,
            pydantic_model=models.SourceType,
        )

        layer = models.Layer(
            id=db_layer.id,
            name=db_layer.name,
            project=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.project,
                model_class=db_models.Project,
                pydantic_model=models.IDModel,
            ),
            date=db_layer.date,
            source_type=source_type,
            source_id=db_layer.source_id,
            catalogue_id=db_layer.catalogue_id,
            data_format=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.data_format,
                model_class=db_models.DataFormat,
                pydantic_model=models.IDModel,
            ),
            data_category=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.data_category,
                model_class=db_models.DataCategory,
                pydantic_model=models.IDModel,
            ),
            legend=db_layer.legend,
            boundary=to_shape(db_layer.boundary) if db_layer.boundary else None,
            bbox=bbox,
            processing_level=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.processing_level,
                model_class=db_models.ProcessingLevel,
                pydantic_model=models.IDModel,
            ),
            area_name=LayerRegistryInterface.get_area_name_instance(
                session=session,
                area_name_id=db_layer.area_name,
            ),
        )

        return layer


class IDModelInterface:
    @staticmethod
    def get_db_entries(session: Session, db_model: object) -> list:
        query = session.query(db_model)

        items = []
        for item in query:
            items.append(
                models.IDModel(id=item.id, last_updated=item.last_updated, name=item.name, object_key=item.object_key)
            )
        return items

    @staticmethod
    def add_model_entry(session: Session, db_model: object, name: str, object_key: str) -> object:
        new_db_item = add_db_item(session=session, db_item=db_model(name=name, object_key=object_key))
        return new_db_item

    @staticmethod
    def convert_to_pydantic_model(db_item: object) -> models.IDModel:
        id_model = models.IDModel(
            id=db_item.id, last_updated=db_item.last_updated, name=db_item.name, object_key=db_item.object_key
        )

        return id_model


class AreaNameModelInterface:
    @staticmethod
    def get_db_entries(session: Session, *_, **__) -> list[models.AreaName]:
        query = session.query(db_models.AreaName)

        items = []
        for item in query:
            area_type = session.get(db_models.AreaType, item.area_type)
            area_type_model = models.IDModel(
                id=area_type.id,
                last_updated=area_type.last_updated,
                name=area_type.name,
                object_key=area_type.object_key,
            )
            items.append(
                models.AreaName(
                    id=item.id,
                    last_updated=item.last_updated,
                    name=item.name,
                    object_key=item.object_key,
                    area_type=area_type_model,
                )
            )
        return items

    @staticmethod
    def add_new_entry(session: Session, name: str, object_key: str, area_type_key: str) -> object:
        area_type = get_db_object_by_key(session=session, db_model=db_models.AreaType, object_key=area_type_key)
        new_db_item = add_db_item(
            session=session, db_item=db_models.AreaName(name=name, object_key=object_key, area_type=area_type.id)
        )
        return new_db_item
