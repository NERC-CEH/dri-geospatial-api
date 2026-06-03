import sqlite3
from datetime import date
from pathlib import Path
from typing import Callable, Generator

import dri_database_models.geospatial as db_models
import pytest
from fastapi.testclient import TestClient
from geoalchemy2 import load_spatialite
from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import Session

from geospatial_api.main import api, app
from geospatial_api.routers import main as main_router

# client = TestClient(app)

# Create a temporary in-memory SQLite engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
SPATIALITE_LIBRARY_PATH = Path(__file__).parents[1].joinpath("mod_spatialite.so.8.1.0")


@pytest.fixture(scope="module")
def engine() -> Engine:
    """Create an in-memory SQLite database engine for the test session."""
    return create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture(scope="function")
def tables(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Create geospatial sqlalchemy tables (dri-database-models) in the in-memory database."""
    schema_name = "geospatial"

    # Register an event listener to ATTACH the 'geospatial' database
    # This gets around the lack of 'geospatial' schema in sqlite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection: sqlite3.Connection, connection_record: Connection) -> None:
        # Ensure the spatialite extension is loaded in order to support the geometry columns
        monkeypatch.setenv("SPATIALITE_LIBRARY_PATH", SPATIALITE_LIBRARY_PATH)
        load_spatialite(dbapi_connection)

        # Attach a second in-memory database with the name 'geospatial'
        # This makes SQLite aware of 'geospatial' as a valid "database" name
        cursor = dbapi_connection.cursor()
        cursor.execute(f"ATTACH DATABASE ':memory:' AS {schema_name}")
        cursor.close()

    # Create the geospatial sqlalchemy tables
    db_models.Base.metadata.create_all(bind=engine)
    yield
    db_models.Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine: Engine, tables: Callable[[], Generator[None, None, None]]) -> Generator[Session, None, None]:
    """Provides a transactional session for each test function, rolling back changes."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)

    # # Add test data to the database session
    session.add(db_models.Project(name="FDRI", object_key="fdri"))
    project = session.query(db_models.Project).filter_by(object_key="fdri").first()

    session.add(db_models.SourceType(name="S3", object_key="s3", base_url="s3://ukceh-fdri-staging-geospatial"))
    source_type = session.query(db_models.SourceType).filter_by(object_key="s3").first()

    session.add(db_models.DataCategoryGroup(name="Topography and Remote Sensing", object_key="topo_rs"))
    category_group = session.query(db_models.DataCategoryGroup).filter_by(object_key="topo_rs").first()
    session.add(
        db_models.DataCategory(name="Digital Surface Model", object_key="dsm", data_category_group=category_group.id)
    )
    data_category = session.query(db_models.DataCategory).filter_by(object_key="dsm").first()

    session.add(db_models.DataFormat(name="Raster", object_key="raster"))
    data_format = session.query(db_models.DataFormat).filter_by(object_key="raster").first()

    session.add(db_models.ProcessingLevel(name="processed", object_key="processed"))
    processing_level = session.query(db_models.ProcessingLevel).filter_by(object_key="processed").first()

    session.add(db_models.LocationType(name="Catchment", object_key="catchment"))
    location_type = session.query(db_models.LocationType).filter_by(object_key="catchment").first()
    session.add(
        db_models.Location(
            name="Tweed",
            object_key="tweed",
            location_type=location_type.id,
            boundary=(
                "POLYGON ((-3.417466 55.510587, -3.417321 55.510616, -3.41727 55.510521, -3.417433 55.510476, "
                "-3.417466 55.510587))"
            ),
        )
    )
    location = session.query(db_models.Location).filter_by(object_key="tweed").first()

    session.add(
        db_models.Layer(
            name="Tweed DSM",
            description="Digital surface model covering the Tweed catchment",
            project=project.id,
            date=date(2026, 3, 20),
            source_type=source_type.id,
            colour_source_id="clipped_tweed_dsm_3857_colourised_cog.tif",
            data_format=data_format.id,
            data_category=data_category.id,
            processing_level=processing_level.id,
            location=location.id,
            legend={
                "type": "range",
                "values": [
                    {
                        "min": {"label": 289.97, "colour": [51, 51, 153]},
                        "max": {"label": 291.61, "colour": [14, 126, 228]},
                    },
                    {
                        "min": {"label": 291.61, "colour": [14, 126, 228]},
                        "max": {"label": 293.25, "colour": [1, 188, 148]},
                    },
                    {
                        "min": {"label": 293.25, "colour": [1, 188, 148]},
                        "max": {"label": 294.9, "colour": [85, 221, 119]},
                    },
                    {
                        "min": {"label": 294.9, "colour": [85, 221, 119]},
                        "max": {"label": 296.54, "colour": [197, 243, 141]},
                    },
                    {
                        "min": {"label": 296.54, "colour": [197, 243, 141]},
                        "max": {"label": 298.18, "colour": [226, 218, 137]},
                    },
                    {
                        "min": {"label": 298.18, "colour": [226, 218, 137]},
                        "max": {"label": 299.83, "colour": [170, 146, 107]},
                    },
                    {
                        "min": {"label": 299.83, "colour": [170, 146, 107]},
                        "max": {"label": 301.47, "colour": [143, 112, 105]},
                    },
                    {
                        "min": {"label": 301.47, "colour": [143, 112, 105]},
                        "max": {"label": 303.11, "colour": [199, 183, 180]},
                    },
                    {
                        "min": {"label": 303.11, "colour": [199, 183, 180]},
                        "max": {"label": 304.76, "colour": [199, 195, 195]},
                    },
                ],
            },
            boundary=(
                "POLYGON ((-3.417466 55.510587, -3.417321 55.510616, -3.41727 55.510521, -3.417433 55.510476, "
                "-3.417466 55.510587))"
            ),
            bbox=(
                "POLYGON ((-3.417467 55.510475, -3.417269 55.510475, -3.417269 55.510617, -3.417467 55.510617, "
                "-3.417467 55.510475))"
            ),
        )
    )

    session.commit()

    yield session

    # Roll back the transaction and close the connection after the test
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provides a TestClient with the 'get_db' dependency overridden to use the test session."""

    def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    api.dependency_overrides[main_router.get_db] = override_get_db_session

    with TestClient(app) as c:
        yield c

    # Clean up overrides after the test
    app.dependency_overrides.clear()


class TestAvailableData:
    def test_available_data(self, client: TestClient) -> None:
        """Test the available_data endpoint returns the expected response."""
        expected_json = [
            {
                "id": 1,
                "name": "Tweed DSM",
                "description": "Digital surface model covering the Tweed catchment",
                "project": {"id": 1, "name": "FDRI", "object_key": "fdri"},
                "date": "2026-03-20",
                "start_date": None,
                "end_date": None,
                "source_type": {
                    "id": 1,
                    "name": "S3",
                    "object_key": "s3",
                    "base_url": "s3://ukceh-fdri-staging-geospatial",
                },
                "data_format": {"id": 1, "name": "Raster", "object_key": "raster"},
                "data_category": {
                    "id": 1,
                    "name": "Digital Surface Model",
                    "object_key": "dsm",
                    "data_category_group": {"id": 1, "name": "Topography and Remote Sensing", "object_key": "topo_rs"},
                },
                "legend": {
                    "type": "range",
                    "values": [
                        {
                            "min": {"label": 289.97, "colour": [51, 51, 153]},
                            "max": {"label": 291.61, "colour": [14, 126, 228]},
                        },
                        {
                            "min": {"label": 291.61, "colour": [14, 126, 228]},
                            "max": {"label": 293.25, "colour": [1, 188, 148]},
                        },
                        {
                            "min": {"label": 293.25, "colour": [1, 188, 148]},
                            "max": {"label": 294.9, "colour": [85, 221, 119]},
                        },
                        {
                            "min": {"label": 294.9, "colour": [85, 221, 119]},
                            "max": {"label": 296.54, "colour": [197, 243, 141]},
                        },
                        {
                            "min": {"label": 296.54, "colour": [197, 243, 141]},
                            "max": {"label": 298.18, "colour": [226, 218, 137]},
                        },
                        {
                            "min": {"label": 298.18, "colour": [226, 218, 137]},
                            "max": {"label": 299.83, "colour": [170, 146, 107]},
                        },
                        {
                            "min": {"label": 299.83, "colour": [170, 146, 107]},
                            "max": {"label": 301.47, "colour": [143, 112, 105]},
                        },
                        {
                            "min": {"label": 301.47, "colour": [143, 112, 105]},
                            "max": {"label": 303.11, "colour": [199, 183, 180]},
                        },
                        {
                            "min": {"label": 303.11, "colour": [199, 183, 180]},
                            "max": {"label": 304.76, "colour": [199, 195, 195]},
                        },
                    ],
                },
                "bbox": {"min_x": -3.417467, "max_x": -3.417269, "min_y": 55.510475, "max_y": 55.510617},
                "processing_level": {"id": 1, "name": "processed", "object_key": "processed"},
                "location": {
                    "id": 1,
                    "name": "Tweed",
                    "object_key": "tweed",
                    "location_type": {"id": 1, "name": "Catchment", "object_key": "catchment"},
                    "bbox": {"min_x": -3.417466, "max_x": -3.41727, "min_y": 55.510476, "max_y": 55.510616},
                    "centroid": {"x": -3.4173733172561627, "y": 55.51054843676313},
                },
                "field_metadata": None,
                "map_center": [-3.417368, 55.510546],
                "colour_source_url": "s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=catchment/location=tweed/data_category=dsm/processing_level=processed/date=2026-03-20/clipped_tweed_dsm_3857_colourised_cog.tif",
                "raw_source_url": None,
            }
        ]

        response = client.get("/api/available_data")

        assert response.status_code == 200
        assert response.json() == expected_json
