import logging

import boto3
from sqlalchemy import Dialect, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from geospatial_api.config import BaseConfig, LocalConfig

logger = logging.getLogger(__name__)

# RDS connection tokens expire after this amount of seconds
TOKEN_EXPIRE_TIME = 900

# Refresh the token 1 minute before it expires
TOKEN_REFRESH_TIME = TOKEN_EXPIRE_TIME - 60


class RDSLogin:
    """
    Utils to handle login to an AWS RDS or local postgres database
    and return a session
    """

    @staticmethod
    def get_db_password(config: LocalConfig | BaseConfig) -> str:
        """
        Handles database passwords.  If running locally then the password is taken
        from the config.  If on AWS then an RDS authentication token is generated.

        Returns:
            The database password or RDS authentication token dependent on environment.
        """

        if isinstance(config, LocalConfig):
            return config.db_password
        else:
            rds_client = boto3.client("rds", region_name=config.AWS_DEFAULT_REGION)
            try:
                token = rds_client.generate_db_auth_token(
                    DBHostname=config.db_host,
                    Port=config.db_port,
                    DBUsername=config.db_user_name,
                    Region=config.AWS_DEFAULT_REGION,
                )
                return token
            except Exception as e:
                logger.error(f"Failed to generate RDS auth token: {str(e)}")
                raise

    @staticmethod
    def get_session_generator(config: LocalConfig | BaseConfig) -> sessionmaker[Session]:
        """
        Creates a factory class to generate new Session objects from a connection pool

        Returns:
        A sessionmaker that can be used to generate new Session objects e.g. by the get_images endpoint
        """
        db_url_object = URL.create(
            drivername="postgresql+psycopg2",
            username=config.db_user_name,
            password=RDSLogin.get_db_password(config),
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
        )
        engine = create_engine(
            db_url_object,
            connect_args={"options": f"-csearch_path={config.db_schema}"},
            echo=False,  # Set to True to do SQL debugging
            pool_size=10,  # The number of persistent connections to keep in the pool. Defaults to 5.
            pool_recycle=TOKEN_REFRESH_TIME,  # Recycle the pool (and connection tokens) after x seconds.
            max_overflow=5,  # The number of extra connections to allow beyond pool_size. Defaults to 10.
            pool_pre_ping=True,  # Enable pre-ping to check connections for liveness before use.
        )

        @event.listens_for(engine, "do_connect")
        def receive_do_connect(
            dialect: Dialect, conn_rec: ConnectionPoolEntry, cargs: list[object], cparams: dict[str, object]
        ) -> None:
            """
            A connection event listener to ensure a new token is generated for the connection
            rather than re-using the old one.
            This is only called when the connection pool is recycled after the TOKEN_REFRESH_TIME.
            """
            cparams["password"] = RDSLogin.get_db_password(config)

        return sessionmaker(autocommit=False, autoflush=False, bind=engine)
