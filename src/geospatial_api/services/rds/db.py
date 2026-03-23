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
    def get_db_entries(session: Session) -> list[models.LayerRegistryItem]:
        layers = []
        query = session.query(db_models.LayerRegistry)
        for item in query:
            bbox = to_shape(item.bbox)

            source_type = LayerRegistryInterface.get_instance(
                session=session,
                model_id=item.source_type,
                model_class=db_models.SourceType,
                pydantic_model=models.SourceType,
                extra_fields=["base_url"],
            )

            layers.append(
                models.LayerRegistryItem(
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
                    source_url=LayerRegistryInterface.construct_source_url(
                        source_type=source_type, source_id=item.source_id
                    ),
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
                )
            )

        return layers

    @staticmethod
    def get_instance(
        session: Session,
        model_id: int,
        model_class: object,
        pydantic_model: object,
        extra_fields: list[str] | None = None,
    ) -> object:
        if extra_fields is None:
            extra_fields = []

        model_instance = session.get(model_class, model_id)

        model_dict = {
            "id": model_instance.id,
            "last_updated": model_instance.last_updated,
            "name": model_instance.name,
            "object_key": model_instance.object_key,
        }

        for extra_field in extra_fields:
            model_dict[extra_field] = getattr(model_instance, extra_field)

        return pydantic_model(**model_dict)

    @staticmethod
    def construct_source_url(source_type: db_models.SourceType, source_id: str) -> str:
        if source_type.object_key.lower() == "s3":
            # TODO: This needs improvement - the source id should be the filename only rather than all the intermediate
            # buckets - need to work out categories and how that applies to s3 keys
            source_url = f"s3://{config.geospatial_data_bucket}/{source_id}"
            return source_url

        # The provided base url may already have the joining /. If this is the case, set the joining character to ""
        join_character = "/"
        if source_type.base_url.endswith("/"):
            join_character = ""

        return f"{source_type.base_url}{join_character}{source_url}"
