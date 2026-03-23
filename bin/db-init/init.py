import os
import time
from datetime import datetime

import psycopg2
import shapely
from build_layer_registry import (
    DSM_DATA_TYPE,
    FDRI_PROJECT,
    POINT_RECORD_TYPE,
    RASTER_TYPE,
    REGION_CATEGORY_NAME,
    REGION_CATEGORY_VALUE,
    VECTOR_TYPE,
    build_layer_registry,
)
from db import GeospatialDatabase

# from dri_database_models.geospatial import (
#     Category,
#     CategoryType,
#     DataFormat,
#     DataType,
#     Layer,
#     Project,
#     SourceType,
# )
from geospatial import Category, CategoryType, DataFormat, DataType, Layer, Project, SourceType
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Get connection details
db_name: str = os.environ.get("POSTGRES_DB", "fdri")
db_user: str = os.environ.get("POSTGRES_USER", "user")
db_password: str = os.environ.get("POSTGRES_PASSWORD", "password")
db_host: str = "postgres"  # Connect to the local Postgres container
db_port: int = int(os.environ.get("POSTGRES_PORT", "5432"))
db_schema: str = os.environ.get("POSTGRES_SCHEMA", "geospatial")


def wait_for_db(max_attempts: int = 20, delay: int = 3) -> None:
    print("Test       Waiting for database to start...")
    for i in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port="5432")
            conn.close()
            print("Database is ready! Connection successful.")
            return
        except psycopg2.OperationalError as e:
            print(f"Attempt {i}/{max_attempts} failed to connect: {e}")
            if i < max_attempts:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    raise Exception("Could not connect to the database after multiple attempts.")


def intialise_db() -> None:
    print("Initialising DB")
    db = GeospatialDatabase(
        db_name=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        schema=db_schema,
    )
    print("Creating tables")
    db.create_tables()

    # Add initial data
    projects = [{"name": "FDRI", "object_key": "fdri", "primary_category_type": REGION_CATEGORY_NAME}]

    data_formats = [
        {"name": "Raster", "object_key": "raster"},
        {"name": "Vector", "object_key": "vector"},
        {"name": "Point record", "object_key": "point_record"},
    ]

    data_types = [{"name": "DEM", "object_key": "dem"}, {"name": "DSM", "object_key": "dsm"}]

    category_types = [{"name": "Region", "object_key": REGION_CATEGORY_NAME}]
    categories = [{"name": "UK", "object_key": REGION_CATEGORY_VALUE, "category_type": REGION_CATEGORY_NAME}]

    source_types = [
        {
            "name": "S3",
            "object_key": "s3",
            "base_url": "s3://ukceh-fdri-staging-geospatial",
        },
        {"name": "EIDC Catalogue", "object_key": "eidc_catalogue", "base_url": "https://catalogue.ceh.ac.uk"},
    ]

    layer_registry = [
        {
            "name": "Tweed DSM",
            "project": "fdri",
            "start_date": "2026-03-20",
            "end_date": "2026-03-20",
            "source_type": "s3",
            "source_id": "clipped_tweed_dsm_3857_colourised_cog.tif",
            "data_format": "raster",
            "data_type": "dsm",
            "resolution": 0.04,
            "legend": [
                {"value": 289.97, "colour": [51, 51, 153]},
                {"value": 291.61, "colour": [14, 126, 228]},
                {"value": 293.25, "colour": [1, 188, 148]},
                {"value": 294.9, "colour": [85, 221, 119]},
                {"value": 296.54, "colour": [197, 243, 141]},
                {"value": 298.18, "colour": [226, 218, 137]},
                {"value": 299.83, "colour": [170, 146, 107]},
                {"value": 301.47, "colour": [143, 112, 105]},
                {"value": 303.11, "colour": [199, 183, 180]},
                {"value": 304.76, "colour": [199, 195, 195]},
            ],
            "boundary": (
                "POLYGON ((-380430.5242783871 7461597.896342132, -380414.411218263 7461603.719226192, "
                "-380408.8039965754 7461584.925790866, -380426.8580180529 7461576.052824679, "
                "-380430.5242783871 7461597.896342132))"
            ),
            "bbox": (
                "POLYGON ((-380430.68545664405 7461576.03170359, -380408.61695664405 7461576.03170359, "
                "-380408.61695664405 7461603.868603591, -380430.68545664405 7461603.868603591, "
                "-380430.68545664405 7461576.03170359))"
            ),
            "primary_category": REGION_CATEGORY_VALUE,
        },
        {
            "name": "COSMOS Sites",
            "project": "fdri",
            "start_date": "2026-03-20",
            "end_date": "2026-03-20",
            "source_type": "s3",
            "source_id": "cosmos_sites.geojson",
            "data_format": "point_record",
            "data_type": "dsm",
            "bbox": (
                "POLYGON ((-380430.68545664405 7461576.03170359, -380408.61695664405 7461576.03170359, "
                "-380408.61695664405 7461603.868603591, -380430.68545664405 7461603.868603591, "
                "-380430.68545664405 7461576.03170359))"
            ),
            "primary_category": REGION_CATEGORY_VALUE,
        }
    ]

    # Create list of category types
    print("Filling CategoryType")
    db.add_db_items([CategoryType(**category_type) for category_type in category_types])

    # Create the project tables, linking to the appropriate category type(s)
    print("Filling Project")
    for project in projects:
        project["primary_category_type"] = db.get_db_item_by_key(
            CategoryType, object_key=project["primary_category_type"]
        ).id

        db.add_db_items([Project(**project)])

    print("Filling Categories")
    for category in categories:
        category["category_type"] = db.get_db_item_by_key(CategoryType, object_key=category["category_type"]).id
        db.add_db_items([Category(**category)])

    print("Filling DataFormat")
    db.add_db_items([DataFormat(**item) for item in data_formats])

    print("Filling data types")
    db.add_db_items([DataType(**item) for item in data_types])

    print("Filling source types")
    db.add_db_items([SourceType(**item) for item in source_types])

    print("Filling Layer Registry")
    for registry_item in layer_registry:
        # registry_item["project"] = db.get_db_item_by_key(Project, object_key=registry_item["project"])
        # registry_item["project_id"] = registry_item["project"].id

        # registry_item["source_type"] = db.get_db_item_by_key(SourceType, object_key=registry_item["source_type"])
        # registry_item['source_type_id'] = registry_item['source_type']

        # registry_item["data_format"] = db.get_db_item_by_key(DataFormat, object_key=registry_item["data_format"])
        # registry_item['data_format_id'] = registry_item['data_format']

        # registry_item["data_type"] = db.get_db_item_by_key(DataType, object_key=registry_item["data_type"])
        # registry_item['data_type_id'] = registry_item['data_type']

        registry_item["project"] = db.get_db_item_by_key(Project, object_key=registry_item["project"]).id
        registry_item["source_type"] = db.get_db_item_by_key(SourceType, object_key=registry_item["source_type"]).id
        registry_item["data_format"] = db.get_db_item_by_key(DataFormat, object_key=registry_item["data_format"]).id
        registry_item["data_type"] = db.get_db_item_by_key(DataType, object_key=registry_item["data_type"]).id

        registry_item["primary_category"] = db.get_db_item_by_key(
            Category, object_key=registry_item["primary_category"]
        ).id

        db.add_db_items([Layer(**registry_item)])

    print("Finished initialising DB")


if __name__ == "__main__":
    wait_for_db()
    intialise_db()
