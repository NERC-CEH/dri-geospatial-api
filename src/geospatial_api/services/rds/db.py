import logging

from dri_database_models import geospatial as db_models
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from geospatial_api import models
from geospatial_api.config import setup_config

logger = logging.getLogger(__name__)

config = setup_config()


class LayerRegistryInterface:
    @staticmethod
    def get_db_entries(session: Session) -> list[models.Layer]:
        layers = []
        query = session.query(db_models.Layer)
        for item in query:
            bbox = to_shape(item.bbox)

            source_type = LayerRegistryInterface.get_instance(
                session=session,
                model_id=item.source_type,
                model_class=db_models.SourceType,
                pydantic_model=models.SourceType,
            )

            layers.append(
                models.Layer(
                    id=item.id,
                    name=item.name,
                    project=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.project,
                        model_class=db_models.Project,
                        pydantic_model=models.IDModel,
                    ),
                    start_date=item.start_date,
                    end_date=item.end_date,
                    source_type=source_type,
                    source_id=item.source_id,
                    catalogue_id=item.catalogue_id,
                    data_format=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.data_format,
                        model_class=db_models.DataFormat,
                        pydantic_model=models.IDModel,
                    ),
                    data_type=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.data_type,
                        model_class=db_models.DataType,
                        pydantic_model=models.IDModel,
                    ),
                    resolution=item.resolution,
                    legend=item.legend,
                    boundary=to_shape(item.boundary) if item.boundary else None,
                    bbox=bbox,
                    centroid=bbox.centroid,
                    primary_category=LayerRegistryInterface.get_category_instance(
                        session=session,
                        category_id=item.primary_category,
                    ),
                )
            )

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

    def get_category_instance(session: Session, category_id: int) -> models.Category:
        category = session.get(db_models.Category, category_id)
        category_type = LayerRegistryInterface.get_instance(
            session=session,
            model_id=category.category_type,
            model_class=db_models.CategoryType,
            pydantic_model=models.IDModel,
        )

        return models.Category(
            id=category.id,
            last_updated=category.last_updated,
            name=category.name,
            object_key=category.object_key,
            category_type=category_type,
        )
