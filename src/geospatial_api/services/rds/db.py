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


def get_db_object_by_primary_key(session: Session, db_model: object, primary_key: int) -> object:
    """Fetch a single database item using the primary key id value

    Args:
        session: The sqlalchemy Session instance
        db_model: The sqlalchemy database class to query
        primary_key: The unique value to be searched for within the `id` column.

    Raises:
        ValueError: The query failed.

    Returns:
        An instance of the sqlalchemy database model corresponding to the requested object key and db_model.

    """
    db_object = session.get(db_model, primary_key)
    if not db_object:
        raise ValueError(
            f"Could not fetch model instance `{str(db_model)} for primary key: {primary_key}. Object may not exist."
        )

    return db_object


class LayerRegistryInterface:
    @staticmethod
    def get_single_layer(session: Session, layer_id: int) -> models.Location:
        db_item = get_db_object_by_primary_key(session=session, db_model=db_models.Layer, primary_key=layer_id)
        return LayerRegistryInterface.convert_layer_to_pydantic_model(session=session, db_layer=db_item)

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
    def get_nested_model_instance(
        session: Session,
        main_model_id: int,
        main_db_model_class: object,
        nested_model_field: str,
        nested_db_model_class: object,
        pydantic_model: object,
    ) -> models.Location:
        main_model = session.get(main_db_model_class, main_model_id)
        nested_pydantic_model = LayerRegistryInterface.get_instance(
            session=session,
            model_id=getattr(main_model, nested_model_field),
            model_class=nested_db_model_class,
            pydantic_model=models.IDModel,
        )

        pydantic_model_data = {
            "id": main_model.id,
            "last_updated": main_model.last_updated,
            "name": main_model.name,
            "object_key": main_model.object_key,
            nested_model_field: nested_pydantic_model,
        }

        # Search for any geometry fields and convert to shapely.Polygon objects
        geometry_fields = [
            field_name
            for (field_name, field_info) in pydantic_model.model_fields.items()
            if field_info.annotation == shapely.Polygon
        ]
        for geometry_field in geometry_fields:
            geometry = to_shape(getattr(main_model, geometry_field))
            pydantic_model_data[geometry_field] = geometry

        return pydantic_model(**pydantic_model_data)

    @staticmethod
    def add_new_layer(
        session: Session,
        name: str,
        project_key: str,
        source_type_key: str,
        data_format_key: str,
        data_category_key: str,
        processing_level_key: str,
        location_key: str,
        description: str | None = None,
        date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        raw_source_id: str | None = None,
        colour_source_id: str | None = None,
        legend: dict[str, Any] | None = None,
        boundary: dict[str, Any] | None = None,
        field_metadata: dict[str, Any] | None = None,
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
            location_key: The object_key value of the Location database model instance it corresponds to.
            raw_source_id: S3 key or similar linking to the raw data source (e.g. geojson file, single band COG
                formatted raster). If not provided then a colour_source_id value is expected . Defaults to None.
            colour_source_id: S3 key or similar linking to the colourised data source (e.g. geojson file, single band
                COG formatted raster). If not provided then a raw_source_id value is expected . Defaults to None.
            legend: JSON string for the legend information. Defaults to None.
            boundary: WKT string for the boundary. This should be in WGS84 and simplified wherever possible.
                Defaults to None.
            field_metadata: JSON string containing metadata for displaying field information from the vector in the UI

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
        location = get_db_object_by_key(session=session, db_model=db_models.Location, object_key=location_key)
        if boundary:
            boundary_geom = shapely.geometry.shape(boundary.features[0])
            boundary_wkt = boundary_geom.wkt
            bbox = shapely.box(*boundary_geom.bounds)
            bbox_wkt = bbox.wkt
        else:
            boundary_wkt = None
            bbox_wkt = None

        new_layer = add_db_item(
            session=session,
            db_item=db_models.Layer(
                name=name,
                description=description,
                project=project.id,
                date=date,
                start_date=start_date,
                end_date=end_date,
                source_type=source_type.id,
                data_format=data_format.id,
                data_category=data_category.id,
                processing_level=processing_level.id,
                location=location.id,
                raw_source_id=raw_source_id,
                colour_source_id=colour_source_id,
                legend=legend,
                boundary=boundary_wkt,
                bbox=bbox_wkt,
                field_metadata=field_metadata,
            ),
        )

        return new_layer

    @staticmethod
    def update_layer(
        session: Session,
        model_id: int,
        name: str | None = None,
        description: str | None = None,
        project_key: str | None = None,
        date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        source_type_key: str | None = None,
        data_format_key: str | None = None,
        data_category_key: str | None = None,
        processing_level_key: str | None = None,
        location_key: str | None = None,
        raw_source_id: str | None = None,
        colour_source_id: str | None = None,
        legend: dict[str, Any] | None = None,
        boundary: dict[str, Any] | None = None,
        field_metadata: dict[str, Any] | None = None,
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
            location_key: The object_key value of the Location database model instance it corresponds to.
            raw_source_id: S3 key or similar linking to the raw data source (e.g. geojson file, single band COG
                formatted raster). If not provided then a colour_source_id value is expected . Defaults to None.
            colour_source_id: S3 key or similar linking to the colourised data source (e.g. geojson file, single band
                COG formatted raster). If not provided then a raw_source_id value is expected . Defaults to None.
            legend: JSON string for the legend information. Defaults to None.
            boundary: WKT string for the boundary. This should be in WGS84 and simplified wherever possible.
                Defaults to None.
            field_metadata: JSON string containing metadata for displaying field information from the vector in the UI

        Returns:
            Layer instance

        """
        layer = get_db_object_by_primary_key(session=session, db_model=db_models.Layer, primary_key=model_id)

        layer.name = name if name is not None else layer.name
        layer.description = (description if description is not None else layer.description,)
        layer.date = (date if date is not None else layer.date,)
        layer.start_date = (start_date if start_date is not None else layer.start_date,)
        layer.end_date = (end_date if end_date is not None else layer.end_date,)

        if project_key is not None:
            project = get_db_object_by_key(session=session, db_model=db_models.Project, object_key=project_key)
            layer.project = project

        if source_type_key is not None:
            source_type = get_db_object_by_key(
                session=session, db_model=db_models.SourceType, object_key=source_type_key
            )
            layer.source_type = source_type.id

        if data_format_key is not None:
            data_format = get_db_object_by_key(
                session=session, db_model=db_models.DataFormat, object_key=data_format_key
            )
            layer.data_format = data_format.id

        if data_category_key is not None:
            data_category = get_db_object_by_key(
                session=session, db_model=db_models.DataCategory, object_key=data_category_key
            )
            layer.data_category = data_category.id

        if processing_level_key is not None:
            processing_level = get_db_object_by_key(
                session=session, db_model=db_models.ProcessingLevel, object_key=processing_level_key
            )
            layer.processing_level = processing_level.id

        if location_key is not None:
            location = get_db_object_by_key(session=session, db_model=db_models.Location, object_key=location_key)
            layer.location = location.id

        if boundary:
            boundary_geom = shapely.geometry.shape(boundary.features[0])
            boundary_wkt = boundary_geom.wkt
            bbox = shapely.box(*boundary_geom.bounds)
            bbox_wkt = bbox.wkt

            layer.boundary = boundary_wkt
            layer.bbox = bbox_wkt

        session.commit()
        return layer

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
            description=db_layer.description,
            project=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.project,
                model_class=db_models.Project,
                pydantic_model=models.IDModel,
            ),
            date=db_layer.date,
            start_date=db_layer.start_date,
            end_date=db_layer.end_date,
            source_type=source_type,
            colour_source_id=db_layer.colour_source_id,
            raw_source_id=db_layer.raw_source_id,
            data_format=LayerRegistryInterface.get_instance(
                session=session,
                model_id=db_layer.data_format,
                model_class=db_models.DataFormat,
                pydantic_model=models.IDModel,
            ),
            data_category=LayerRegistryInterface.get_nested_model_instance(
                session=session,
                main_model_id=db_layer.data_category,
                main_db_model_class=db_models.DataCategory,
                nested_model_field="data_category_group",
                nested_db_model_class=db_models.DataCategoryGroup,
                pydantic_model=models.DataCategory,
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
            location=LayerRegistryInterface.get_nested_model_instance(
                session=session,
                main_model_id=db_layer.location,
                main_db_model_class=db_models.Location,
                nested_model_field="location_type",
                nested_db_model_class=db_models.LocationType,
                pydantic_model=models.Location,
            ),
            field_metadata=db_layer.field_metadata,
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
    def update_model_entry(
        session: Session, db_model: object, model_id: int, name: str | None = None, object_key: str | None = None
    ) -> object:
        """Update an existing model entry for any database model that corresponds to the pydantic IDModel base class."""
        db_item = get_db_object_by_primary_key(session=session, db_model=db_model, primary_key=model_id)

        db_item.name = name if name else db_item.name
        db_item.object_key = object_key if object_key else db_item.object_key

        session.commit()

        return db_item

    @staticmethod
    def convert_to_pydantic_model(db_item: object) -> models.IDModel:
        """Convert the db instance to a pydantic IDModel."""
        id_model = models.IDModel(
            id=db_item.id, last_updated=db_item.last_updated, name=db_item.name, object_key=db_item.object_key
        )

        return id_model


class SourceTypeModelInterface:
    @staticmethod
    def get_db_entries(session: Session, *_, **__) -> list:
        """Fetch all items for the SourceType database model."""
        query = session.query(db_models.SourceType)

        items = []
        for item in query:
            items.append(SourceTypeModelInterface.convert_to_pydantic_model(db_item=item))
        return items

    @staticmethod
    def convert_to_pydantic_model(db_item: object) -> models.SourceType:
        """Convert the db instance to a pydantic SourceType."""
        source_type = models.SourceType(
            id=db_item.id, last_updated=db_item.last_updated, name=db_item.name, object_key=db_item.object_key
        )

        return source_type

    @staticmethod
    def add_new_entry(
        session: Session,
        name: str,
        object_key: str,
        base_url: str,
    ) -> object:
        """Add a new SourceType entry to the database."""
        new_db_item = add_db_item(
            session=session,
            db_item=db_models.Location(name=name, object_key=object_key, base_url=base_url),
        )
        return new_db_item

    @staticmethod
    def update_model_entry(
        session: Session,
        model_id: int,
        name: str | None = None,
        object_key: str | None = None,
        base_url: str | None = None,
    ) -> object:
        """Update an existing SourceType model entry."""
        db_item = get_db_object_by_primary_key(session=session, db_model=db_models.SourceType, primary_key=model_id)

        db_item.name = name if name is not None else db_item.name
        db_item.object_key = object_key if object_key is not None else db_item.object_key
        db_item.base_url = base_url if base_url is not None else db_item.base_url

        session.commit()

        return db_item


class LocationModelInterface:
    @staticmethod
    def get_single_location(session: Session, location_id: int) -> models.Location:
        db_item = get_db_object_by_primary_key(session=session, db_model=db_models.Location, primary_key=location_id)
        return LocationModelInterface.convert_db_item_to_pydantic_model(session=session, db_item=db_item)

    @staticmethod
    def get_db_entries(session: Session, *_, **__) -> list[models.Location]:
        """List all entries within the Location database table."""
        query = session.query(db_models.Location)

        items = []
        for item in query:
            items.append(LocationModelInterface.convert_db_item_to_pydantic_model(session=session, db_item=item))
        return items

    @staticmethod
    def convert_db_item_to_pydantic_model(session: Session, db_item: db_models.Location) -> models.Location:
        location_type = session.get(db_models.LocationType, db_item.location_type)
        location_type_model = models.IDModel(
            id=location_type.id,
            last_updated=location_type.last_updated,
            name=location_type.name,
            object_key=location_type.object_key,
        )

        return models.Location(
            id=db_item.id,
            last_updated=db_item.last_updated,
            name=db_item.name,
            object_key=db_item.object_key,
            location_type=location_type_model,
            boundary=to_shape(db_item.boundary),
        )

    @staticmethod
    def add_new_entry(
        session: Session, name: str, object_key: str, location_type_key: str, boundary: dict[str, Any]
    ) -> object:
        """Add a new Location entry to the database."""
        location_type = get_db_object_by_key(
            session=session, db_model=db_models.LocationType, object_key=location_type_key
        )

        boundary_geom = shapely.geometry.shape(boundary.features[0])
        boundary_wkt = boundary_geom.wkt

        new_db_item = add_db_item(
            session=session,
            db_item=db_models.Location(
                name=name, object_key=object_key, location_type=location_type.id, boundary=boundary_wkt
            ),
        )
        return new_db_item

    @staticmethod
    def update_entry(
        session: Session,
        model_id: int,
        name: str | None = None,
        object_key: str | None = None,
        location_type_key: str | None = None,
        boundary: dict[str, Any] | None = None,
    ) -> object:
        """Add a new Location entry to the database."""
        location_instance = get_db_object_by_primary_key(
            session=session, db_model=db_models.Location, primary_key=model_id
        )

        location_instance.name = name if name is not None else location_instance.name
        location_instance.object_key = object_key if object_key is not None else location_instance.object_key

        if location_type_key is not None:
            location_type = get_db_object_by_key(
                session=session, db_model=db_models.LocationType, object_key=location_type_key
            )
            location_instance.location_type = location_type.id

        if boundary is not None:
            boundary_geom = shapely.geometry.shape(boundary.features[0])
            boundary_wkt = boundary_geom.wkt
            location_instance.boundary = boundary_wkt

        session.commit()
        return location_instance


class DataCategoryModelInterface:
    @staticmethod
    def get_db_entries(session: Session, *_, **__) -> list[models.Location]:
        """List all entries within the DataCategory database table."""
        query = session.query(db_models.DataCategory)

        items = []
        for item in query:
            category_group = session.get(db_models.DataCategoryGroup, item.data_category_group)
            category_group_model = models.IDModel(
                id=category_group.id,
                last_updated=category_group.last_updated,
                name=category_group.name,
                object_key=category_group.object_key,
            )
            items.append(
                models.DataCategory(
                    id=item.id,
                    last_updated=item.last_updated,
                    name=item.name,
                    object_key=item.object_key,
                    data_category_group=category_group_model,
                )
            )
        return items

    @staticmethod
    def convert_db_item_to_pydantic_model(session: Session, db_item: db_models.DataCategory) -> models.DataCategory:
        category_group_db_item = session.get(db_models.DataCategoryGroup, db_item.data_category_group)
        category_group_model = models.IDModel(
            id=category_group_db_item.id,
            last_updated=category_group_db_item.last_updated,
            name=category_group_db_item.name,
            object_key=category_group_db_item.object_key,
        )

        return models.DataCategory(
            id=db_item.id,
            last_updated=db_item.last_updated,
            name=db_item.name,
            object_key=db_item.object_key,
            data_category_group=category_group_model,
        )

    @staticmethod
    def add_new_entry(session: Session, name: str, object_key: str, data_category_group_key: str) -> object:
        """Add a new DataCategory entry to the database."""
        data_category_group = get_db_object_by_key(
            session=session, db_model=db_models.DataCategoryGroup, object_key=data_category_group_key
        )
        new_db_item = add_db_item(
            session=session,
            db_item=db_models.DataCategory(
                name=name, object_key=object_key, data_category_group=data_category_group.id
            ),
        )
        return new_db_item

    @staticmethod
    def update_entry(
        session: Session, model_id: int, name: str, object_key: str, data_category_group_key: str
    ) -> object:
        """Add a new DataCategory entry to the database."""
        data_category_instance = get_db_object_by_primary_key(
            session=session, db_model=db_models.DataCategory, primary_key=model_id
        )

        data_category_instance.name = name if name is not None else data_category_instance.name
        data_category_instance.object_key = object_key if object_key is not None else data_category_instance.object_key

        if data_category_group_key is not None:
            data_category_group = get_db_object_by_key(
                session=session, db_model=db_models.DataCategoryGroup, object_key=data_category_group_key
            )
            data_category_instance.data_category_group = data_category_group.id

        session.commit()
        return data_category_instance
