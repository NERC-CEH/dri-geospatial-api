import os
import time

import psycopg2
from db import GeospatialDatabase
from dri_database_models import geospatial

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

    data_category_groups = [
        {"name": "Topography and Remote Sensing", "object_key": "topo_rs"},
        {"name": "Geology and Soils", "object_key": "geology_soils"},
        {"name": "Hydrology", "object_key": "hydrology"},
    ]

    data_categories = [
        {"name": "Digital Elevation Model", "object_key": "dem", "data_category_group": "topo_rs"},
        {"name": "Digital Surface Model", "object_key": "dsm", "data_category_group": "topo_rs"},
        {"name": "Soil Moisture", "object_key": "soil_moisture", "data_category_group": "geology_soils"},
        {"name": "Flow Monitoring", "object_key": "flow_monitoring", "data_category_group": "hydrology"},
    ]

    data_formats = [
        {"name": "Raster", "object_key": "raster"},
        {"name": "Vector", "object_key": "vector"},
        {"name": "Point record", "object_key": "point_record"},
    ]

    processing_levels = [{"name": "Processed", "object_key": "processed"}, {"name": "Raw", "object_key": "raw"}]

    location_types = [
        {"name": "National", "object_key": "national"},
        {"name": "Region", "object_key": "region"},
        {"name": "Catchment", "object_key": "catchment"},
    ]

    locations = [
        {
            "name": "UK",
            "object_key": "uk",
            "location_type": "national",
            "boundary": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
        },
        {
            "name": "Tweed",
            "object_key": "tweed",
            "location_type": "catchment",
            "boundary": (
                "POLYGON ((-3.417466 55.510587, -3.417321 55.510616, -3.41727 55.510521, -3.417433 55.510476, "
                "-3.417466 55.510587))"
            ),
        },
    ]

    source_types = [
        {
            "name": "S3",
            "object_key": "s3",
            "base_url": "s3://ukceh-fdri-staging-geospatial",
        },
        {"name": "Metadata API", "object_key": "metadata_api", "base_url": "https://dri-metadata-api.dri.ceh.ac.uk"},
        {"name": "EIDC Catalogue", "object_key": "eidc_catalogue", "base_url": "https://catalogue.ceh.ac.uk"},
    ]

    layers = [
        {
            "name": "Tweed DSM",
            "description": "Digital surface model covering the Tweed catchment",
            "project": "fdri",
            "date": "2026-03-20",
            "source_type": "s3",
            "colour_source_id": "clipped_tweed_dsm_3857_colourised_cog.tif",
            "data_format": "raster",
            "data_category": "dsm",
            "processing_level": "processed",
            "location": "tweed",
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
            "start_date": "2026-03-20",
            "end_date": "2026-05-01",
            "source_type": "metadata_api",
            "raw_source_id": (
                "id/network/cosmos?_projection=contains.label,contains.comment,contains.identifier,contains."
                "hasGeometry.*"
            ),
            "data_format": "vector",
            "data_category": "soil_moisture",
            "processing_level": "processed",
            "location": "uk",
            "boundary": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
            "bbox": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
            "field_metadata": [
                {
                    "display_label": "Name",
                    "key": "name",
                    "field_keys": [{"key": "label", "type": "list", "index": 0}],
                    "data_type": "string",
                },
                {
                    "display_label": "Name",
                    "key": "geometry",
                    "field_keys": [
                        {"key": "hasGeometry", "type": "wkt_list", "index": None},
                    ],
                    "data_type": "string",
                },
            ],
        },
        {
            "name": "EA Flow Gaugings",
            "project": "fdri",
            "start_date": "2024-01-01",
            "end_date": None,
            "source_type": "metadata_api",
            "raw_source_id": (
                "id/network/ea-manual-sites?_projection=contains.label,contains.comment,contains.identifier,"
                "contains.hasGeometry.*"
            ),
            "data_format": "vector",
            "data_category": "flow_monitoring",
            "processing_level": "raw",
            "location": "uk",
            "boundary": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
            "bbox": (
                "POLYGON ((-7.291954 50.03266, 1.034231 50.03266, 1.034231 56.914403, -7.291954 56.914403, "
                "-7.291954 50.03266))"
            ),
            "field_metadata": [
                {
                    "display_label": "Name",
                    "key": "name",
                    "field_keys": [{"key": "label", "type": "list", "index": 0}],
                    "data_type": "string",
                },
                {
                    "display_label": "Name",
                    "key": "geometry",
                    "field_keys": [
                        {"key": "hasGeometry", "type": "wkt_list", "index": None},
                    ],
                    "data_type": "string",
                },
            ],
        },
    ]

    print("Filling Projects")
    db.add_db_items([geospatial.Project(**item) for item in projects])

    print("Filling Data Category Groups")
    db.add_db_items([geospatial.DataCategoryGroup(**item) for item in data_category_groups])

    print("Filling Data Categories")
    for data_category in data_categories:
        category_group = db.get_db_item_by_key(
            geospatial.DataCategoryGroup, object_key=data_category["data_category_group"]
        )
        data_category["data_category_group"] = category_group.id
        db.add_db_items([geospatial.DataCategory(**data_category)])

    print("Filling Data Formats")
    db.add_db_items([geospatial.DataFormat(**item) for item in data_formats])

    print("Filling Processing Levels")
    db.add_db_items([geospatial.ProcessingLevel(**item) for item in processing_levels])

    print("Filling Area Types")
    db.add_db_items([geospatial.LocationType(**item) for item in location_types])

    print("Filling Area Names")
    for location in locations:
        location_type = db.get_db_item_by_key(geospatial.LocationType, object_key=location["location_type"])
        location["location_type"] = location_type.id
        db.add_db_items([geospatial.Location(**location)])

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
        layer["location"] = db.get_db_item_by_key(geospatial.Location, object_key=layer["location"]).id

        db.add_db_items([geospatial.Layer(**layer)])

    print("Finished initialising DB")


if __name__ == "__main__":
    wait_for_db()
    intialise_db()
