from datetime import datetime
from typing import Optional

from dri_database_models.base import Base, pk
from geoalchemy2 import Geometry
from sqlalchemy import JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class CategoryType(Base):
    __tablename__ = "category_type"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class Category(Base):
    __tablename__ = "category"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.
    category_type: Mapped[int] = mapped_column(ForeignKey("geospatial.category_type.id"))


class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.
    primary_category_type: Mapped[list[int]] = mapped_column(ForeignKey("geospatial.category_type.id"))
    secondary_category_type: Mapped[Optional[int]] = mapped_column(ForeignKey("geospatial.category_type.id"))
    tertiary_category_type: Mapped[Optional[int]] = mapped_column(ForeignKey("geospatial.category_type.id"))


class DataFormat(Base):
    __tablename__ = "data_format"
    __table_args__ = {"schema": "geospatial"}

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    object_key: Mapped[str]  # Value to associate with the display name, used for the S3 key etc.


class DataType(Base):
    __tablename__ = "data_type"
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


class Layer(Base):
    __tablename__ = "layer"
    __table_args__ = ({"schema": "geospatial"},)

    id: Mapped[pk]
    last_updated: Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    name: Mapped[str]  # The display name
    project: Mapped[int] = mapped_column(ForeignKey("geospatial.project.id"))
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    source_type: Mapped[int] = mapped_column(ForeignKey("geospatial.source_type.id"))
    source_id: Mapped[str]
    catalogue_id: Mapped[Optional[str]]
    data_format: Mapped[int] = mapped_column(ForeignKey("geospatial.data_format.id"))
    data_type: Mapped[int] = mapped_column(ForeignKey("geospatial.data_type.id"))
    resolution: Mapped[Optional[float]]
    legend: Mapped[Optional[JSON]] = mapped_column(type_=JSON)
    boundary: Mapped[Optional[Geometry]] = mapped_column(type_=Geometry)
    bbox: Mapped[Geometry] = mapped_column(type_=Geometry)
    primary_category: Mapped[int] = mapped_column(ForeignKey("geospatial.category.id"))
    secondary_category: Mapped[Optional[int]] = mapped_column(ForeignKey("geospatial.category.id"))
    tertiary_category: Mapped[Optional[int]] = mapped_column(ForeignKey("geospatial.category.id"))
