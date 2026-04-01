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
                    date=item.date,
                    source_type=source_type,
                    source_id=item.source_id,
                    catalogue_id=item.catalogue_id,
                    data_format=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.data_format,
                        model_class=db_models.DataFormat,
                        pydantic_model=models.IDModel,
                    ),
                    data_category=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.data_category,
                        model_class=db_models.DataCategory,
                        pydantic_model=models.IDModel,
                    ),
                    legend=item.legend,
                    boundary=to_shape(item.boundary) if item.boundary else None,
                    bbox=bbox,
                    processing_level=LayerRegistryInterface.get_instance(
                        session=session,
                        model_id=item.processing_level,
                        model_class=db_models.ProcessingLevel,
                        pydantic_model=models.IDModel,
                    ),
                    area_name=LayerRegistryInterface.get_area_name_instance(
                        session=session,
                        area_name_id=item.area_name,
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

    