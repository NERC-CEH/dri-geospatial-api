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
    """Adds a new item to the database.

    Args:
        session: The sqlalchemy Session instance
        db_item: The item to be added to the database. This should be an instantiated version of the sqlalchemy class
            for the relevant database table. For example the Layer class in dri_database_models.geospatial

    Returns:
        The database item provided to the function, updated with the corresponding primary key (id) and any other db
        controlled fields (e.g. last_updated).

    """
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
    """Fetch a single database item using the object_key value

    This expects the database model (table) to be queried to contain the field `object_key` and for the object_key
    value to be unique.

    Args:
        session: The sqlalchemy Session instance
        db_model: The sqlalchemy database class to query
        object_key: The unique value to be searched for within the `object_key` column.

    Raises:
        ValueError: The query failed.

    Returns:
        An instance of the sqlalchemy database model corresponding to the requested object key and db_model.

    """
    db_object = session.query(db_model).filter_by(object_key=object_key).first()
    if not db_object:
        raise ValueError(
            f"Could not fetch model instance `{str(db_model)} for key: {object_key}. Object may not exist."
        )

    return db_object


class LayerRegistryInterface:
    @staticmethod
    def get_db_entries(session: Session) -> list[models.Layer]:
        """Fetch all entries for the Layer model, converted to the corresponding pydantic model."""
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
        """Fetch a single db item, converted to the corresponding pydantic model. Note that it is assumed there are
        no sub-dependent models - each field maps directly to a single value.

        Args:
            session: The sqlalchemy Session instance.
            model_id: The numeric primary key id of the model instance to fetch
            model_class: The sqlalchemy database class to query
            pydantic_model: The corresponding pydantic model to use for the returned database data

        Returns:
            Pydantic model of the queried database model instance.

        """
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
        raw_source_id: str | None = None,
        colour_source_id: str | None = None,
        legend: dict[str, Any] | None = None,
        boundary: dict[str, Any] | None = None,
    ) -> db_models.Layer:
        """Adds a new Layer instance to the database.

        Args:
            session: The sqlalchemy Session instance.
            name: The name of the layer
            project_key: The object_key value of the Project model instance to correspond to.
            date: The date to associate with the layer
            source_type_key: The object_key value of the SourceType database model instance it corresponds to.
            data_format_key: The object_key value of the DataFormat database model instance it corresponds to.
            data_category_key: The object_key value of the DataCategory database model instance it corresponds to.
            processing_level_key: The object_key value of the ProcessingLevel database model instance it corresponds to.
            area_name_key: The object_key value of the AreaName database model instance it corresponds to.
            raw_source_id: S3 key or similar linking to the raw data source (e.g. geojson file, single band COG
                formatted raster). If not provided then a colour_source_id value is expected . Defaults to None.
            colour_source_id: S3 key or similar linking to the colourised data source (e.g. geojson file, single band
                COG formatted raster). If not provided then a raw_source_id value is expected . Defaults to None.
            legend: JSON string for the legend information. Defaults to None.
            boundary: WKT string for the boundary. This should be in WGS84 and simplified wherever possible.
                Defaults to None.

        Returns:
            Layer instance

        """
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
                raw_source_id=raw_source_id,
                colour_source_id=colour_source_id,
                legend=legend,
                boundary=boundary_geom.wkt,
                bbox=bbox.wkt,
            ),
        )

        return new_layer

    @staticmethod
    def convert_layer_to_pydantic_model(session: Session, db_layer: db_models.Layer) -> models.Layer:
        """Converts a the database Layer model into it's pydantic model equivalent."""
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
            colour_source_id=db_layer.colour_source_id,
            raw_source_id=db_layer.raw_source_id,
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
        """Fetch all items for any database model that fits within the pydantic IDModel baseclass."""
        query = session.query(db_model)

        items = []
        for item in query:
            items.append(
                models.IDModel(id=item.id, last_updated=item.last_updated, name=item.name, object_key=item.object_key)
            )
        return items

    @staticmethod
    def add_model_entry(session: Session, db_model: object, name: str, object_key: str) -> object:
        """Add a new model entry for any database model that corresponds to the pydantic IDModel base class."""
        new_db_item = add_db_item(session=session, db_item=db_model(name=name, object_key=object_key))
        return new_db_item

    @staticmethod
    def convert_to_pydantic_model(db_item: object) -> models.IDModel:
        """Convert the db instance to a pydantic IDModel."""
        id_model = models.IDModel(
            id=db_item.id, last_updated=db_item.last_updated, name=db_item.name, object_key=db_item.object_key
        )

        return id_model


class AreaNameModelInterface:
    @staticmethod
    def get_db_entries(session: Session, *_, **__) -> list[models.AreaName]:
        """List all entries within the AreaName database table."""
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
        """Add a new AreaName entry to the database."""
        area_type = get_db_object_by_key(session=session, db_model=db_models.AreaType, object_key=area_type_key)
        new_db_item = add_db_item(
            session=session, db_item=db_models.AreaName(name=name, object_key=object_key, area_type=area_type.id)
        )
        return new_db_item
