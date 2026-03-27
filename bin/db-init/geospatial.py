from datetime import datetime
from typing import Optional

from dri_database_models.base import Base, pk
from geoalchemy2 import Geometry
from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.
    # category_hierachy: Mapped[MutableList] = mapped_column(MutableList.as_mutable(list[str]))


class DataFormat(Base):
    __tablename__ = "data_format"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class DataCategory(Base):
    __tablename__ = "data_category"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class SourceType(Base):
    __tablename__ = "source_type"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    base_url: Mapped[str]  # The base url (e.g. s3:// or "https://catalogue.ceh.ac.uk/")
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class ProcessingLevel(Base):
    __tablename__ = "processing_level"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class AreaType(Base):
    __tablename__ = "area_type"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class AreaName(Base):
    __tablename__ = "area_name"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.
    area_type: Mapped[int] =  mapped_column(ForeignKey("geospatial.area_type.id"))


class Layer(Base):
    __tablename__ = "layer"
    __table_args__ = ({"schema": "geospatial"},)

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    project: Mapped[int] = mapped_column(ForeignKey("geospatial.project.id"))
    date: Mapped[datetime]
    source_type: Mapped[int] = mapped_column(ForeignKey("geospatial.source_type.id"))
    source_id: Mapped[str]
    catalogue_id: Mapped[Optional[str]]
    data_format: Mapped[int] = mapped_column(ForeignKey("geospatial.data_format.id"))
    data_category: Mapped[int] = mapped_column(ForeignKey("geospatial.data_category.id"))
    resolution: Mapped[Optional[float]]
    legend: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    boundary: Mapped[Optional[Geometry]] = mapped_column(type_=Geometry)
    bbox: Mapped[Geometry] = mapped_column(type_=Geometry)
    processing_level: Mapped[int] = mapped_column(ForeignKey("geospatial.processing_level.id"))
    area_name: Mapped[int] = mapped_column(ForeignKey("geospatial.area_name.id"))
