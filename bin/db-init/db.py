import logging

from dri_database_models.geospatial import Base
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class GeospatialDatabase:
    def __init__(self, user: str, password: str, host: str, port: int, db_name: str, schema: str, echo: bool = True):
        self.database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
        self.engine = create_engine(self.database_url, connect_args={"options": f"-csearch_path={schema}"}, echo=echo)
        self.session_factory = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def drop_tables(self) -> None:
        Base.metadata.drop_all(self.engine)

    def add_db_items(self, db_items: list) -> None:
        session = self.session_factory()
        try:
            session.add_all(db_items)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("Failed to write data to database.")
            logger.exception(e)
            raise
        finally:
            session.close()

    def get_db_item_by_key(self, db_table_class: object, object_key: str) -> object | None:
        session = self.session_factory()
        try:
            return session.query(db_table_class).filter_by(object_key=object_key).first()
        finally:
            session.close()
