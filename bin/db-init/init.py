import os
import time

from dri_database_models import geospatial
import psycopg2
from db import GeospatialDatabase

RASTER_TYPE = "raster"
VECTOR_TYPE = "vector"
POINT_RECORD_TYPE = "point_record"

FDRI_PROJECT = "fdri"
DSM_DATA_TYPE = "dsm"
LEGEND_SUFFIX = "_legend.json"


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
    print("Clearing any existing data.")
    db.drop_tables()

    print("Creating tables")
    db.create_tables()

    # Add initial data
    projects = [{"name": "FDRI", "object_key": "fdri"}]

    data_categories = [
        {"name": "DEM", "object_key": "dem"},
        {"name": "DSM", "object_key": "dsm"},
        {"name": "Stations", "object_key": "stations"},
    ]

    data_formats = [
        {"name": "Raster", "object_key": "raster"},
        {"name": "Vector", "object_key": "vector"},
        {"name": "Point record", "object_key": "point_record"},
    ]

    processing_levels = [{"name": "Processed", "object_key": "processed"}, {"name": "Raw", "object_key": "raw"}]

    area_types = [
        {"name": "National", "object_key": "national"},
        {"name": "Region", "object_key": "region"},
        {"name": "Catchment", "object_key": "catchment"},
    ]

    area_names = [
        {"name": "UK", "object_key": "uk", "area_type": "national"},
        {"name": "Tweed", "object_key": "tweed", "area_type": "catchment"},
        {"name": "Chess", "object_key": "chess", "area_type": "catchment"},
        {"name": "Severn", "object_key": "severn", "area_type": "catchment"},
    ]

    source_types = [
        {
            "name": "S3",
            "object_key": "s3",
            "base_url": "s3://ukceh-fdri-staging-geospatial",
        },
        {"name": "EIDC Catalogue", "object_key": "eidc_catalogue", "base_url": "https://catalogue.ceh.ac.uk"},
    ]

    layers = [
        {
            "name": "Tweed DSM",
            "project": "fdri",
            "date": "2026-03-20",
            "source_type": "s3",
            "source_id": "clipped_tweed_dsm_3857_colourised_cog.tif",
            "data_format": "raster",
            "data_category": "dsm",
            "processing_level": "processed",
            "area_name": "tweed",
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
                "POLYGON ((-3.417466 55.510587, -3.417321 55.510616, -3.41727 55.510521, -3.417433 55.510476, "
                "-3.417466 55.510587))"
            ),
            "bbox": (
                "POLYGON ((-3.417467 55.510475, -3.417269 55.510475, -3.417269 55.510617, -3.417467 55.510617, "
                "-3.417467 55.510475))"
            ),
        },
        {
            "name": "Cosmos Sites",
            "project": "fdri",
            "date": "2026-03-20",
            "source_type": "s3",
            "source_id": "cosmos_sites.geojson",
            "data_format": "vector",
            "data_category": "stations",
            "processing_level": "processed",
            "area_name": "uk",
            "boundary": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
            "bbox": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
        },
    ]

    print("Filling Projects")
    db.add_db_items([geospatial.Project(**item) for item in projects])

    print("Filling Data Categories")
    db.add_db_items([geospatial.DataCategory(**item) for item in data_categories])

    print("Filling Data Formats")
    db.add_db_items([geospatial.DataFormat(**item) for item in data_formats])

    print("Filling Processing Levels")
    db.add_db_items([geospatial.ProcessingLevel(**item) for item in processing_levels])

    print("Filling Area Types")
    db.add_db_items([geospatial.AreaType(**item) for item in area_types])

    print("Filling Area Names")
    for area_name in area_names:
        area_type = db.get_db_item_by_key(geospatial.AreaType, object_key=area_name["area_type"])
        area_name["area_type"] = area_type.id
        db.add_db_items([geospatial.AreaName(**area_name)])

    print("Filling source types")
    db.add_db_items([geospatial.SourceType(**item) for item in source_types])

    print("Filling Layer Registry")
    for layer in layers:
        layer["project"] = db.get_db_item_by_key(geospatial.Project, object_key=layer["project"]).id
        layer["source_type"] = db.get_db_item_by_key(geospatial.SourceType, object_key=layer["source_type"]).id
        layer["data_format"] = db.get_db_item_by_key(geospatial.DataFormat, object_key=layer["data_format"]).id
        layer["data_category"] = db.get_db_item_by_key(geospatial.DataCategory, object_key=layer["data_category"]).id
        layer["processing_level"] = db.get_db_item_by_key(
            geospatial.ProcessingLevel, object_key=layer["processing_level"]
        ).id
        layer["area_name"] = db.get_db_item_by_key(geospatial.AreaName, object_key=layer["area_name"]).id

        db.add_db_items([geospatial.Layer(**layer)])

    print("Finished initialising DB")


if __name__ == "__main__":
    wait_for_db()
    intialise_db()
