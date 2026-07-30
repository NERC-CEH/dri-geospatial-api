from datetime import date

import shapely

from geospatial_api.models import DataCategory, IDModel, Layer, Location, SourceType


class TestLocation:
    def test_to_json_response(self) -> None:
        location = Location(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Location 1",
            object_key="location_1",
            location_type=IDModel(
                id=1,
                last_updated=date(2026, 1, 1),
                name="Location Type 1",
                object_key="location_type_1",
            ),
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        )
        expected_json = {
            "id": 1,
            "name": "Location 1",
            "object_key": "location_1",
            "location_type": {"id": 1, "name": "Location Type 1", "object_key": "location_type_1"},
            "bbox": {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0},
            "centroid": {"x": 0.5, "y": 0.5},
        }

        json_response = location.to_json_response()

        assert json_response == expected_json


class TestLayer:
    def test_to_json_response(self) -> None:
        project = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Project 1",
            object_key="project_1",
        )
        source_type = SourceType(
            id=1, last_updated=date(2026, 1, 1), name="S3", object_key="s3", base_url="s3://geospatial_s3_bucket"
        )

        data_format = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raster",
            object_key="raster",
        )

        data_category = DataCategory(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Category 1",
            object_key="category_1",
            data_category_group=IDModel(
                id=1, last_updated=date(2026, 1, 1), name="Category group 1", object_key="group_1"
            ),
        )

        location = Location(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Location 1",
            object_key="location_1",
            location_type=IDModel(
                id=1,
                last_updated=date(2026, 1, 1),
                name="Location Type 1",
                object_key="location_type_1",
            ),
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        )

        processing_level = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raw",
            object_key="raw",
        )

        layer = Layer(
            id=1,
            name="Layer 1",
            description="Add description here",
            project=project,
            date=date(2026, 1, 1),
            start_date=None,
            end_date=None,
            source_type=source_type,
            colour_source_id="colour_raster.tif",
            raw_source_id="greyscale_raster.tif",
            layer_id=None,
            data_format=data_format,
            data_category=data_category,
            legend={
                "type": "range",
                "values": [
                    {
                        "min": {"value": 289.97, "colour": [51, 51, 153]},
                        "max": {"value": 291.61, "colour": [14, 126, 228]},
                    },
                    {
                        "min": {"value": 291.61, "colour": [14, 126, 228]},
                        "max": {"value": 293.25, "colour": [1, 188, 148]},
                    },
                ],
            },
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            bbox=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            processing_level=processing_level,
            location=location,
            field_metadata=None,
            filter_metadata=None,
        )

        expected_response = {
            "id": 1,
            "name": "Layer 1",
            "description": "Add description here",
            "project": {"id": 1, "name": "Project 1", "object_key": "project_1"},
            "date": "2026-01-01",
            "start_date": None,
            "end_date": None,
            "source_type": {"id": 1, "name": "S3", "object_key": "s3", "base_url": "s3://geospatial_s3_bucket"},
            "data_format": {"id": 1, "name": "Raster", "object_key": "raster"},
            "data_category": {
                "id": 1,
                "name": "Category 1",
                "object_key": "category_1",
                "data_category_group": {"id": 1, "name": "Category group 1", "object_key": "group_1"},
            },
            "layer_id": None,
            "legend": {
                "type": "range",
                "values": [
                    {
                        "min": {"value": 289.97, "colour": [51, 51, 153]},
                        "max": {"value": 291.61, "colour": [14, 126, 228]},
                    },
                    {
                        "min": {"value": 291.61, "colour": [14, 126, 228]},
                        "max": {"value": 293.25, "colour": [1, 188, 148]},
                    },
                ],
            },
            "bbox": {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0},
            "processing_level": {"id": 1, "name": "Raw", "object_key": "raw"},
            "location": {
                "id": 1,
                "name": "Location 1",
                "object_key": "location_1",
                "location_type": {"id": 1, "name": "Location Type 1", "object_key": "location_type_1"},
                "bbox": {"min_x": 0.0, "max_x": 1.0, "min_y": 0.0, "max_y": 1.0},
                "centroid": {"x": 0.5, "y": 0.5},
            },
            "field_metadata": None,
            "filter_metadata": None,
            "map_center": [0.5, 0.5],
            "colour_source_url": "s3://geospatial_s3_bucket/project=project_1/location_type=location_type_1/location=location_1/data_category=category_1/processing_level=raw/date=2026-01-01/colour_raster.tif",
            "raw_source_url": "s3://geospatial_s3_bucket/project=project_1/location_type=location_type_1/location=location_1/data_category=category_1/processing_level=raw/date=2026-01-01/greyscale_raster.tif",
        }

        json_response = layer.to_json_response()

        assert json_response == expected_response

    def test_get_source_url_start_and_end_date(self) -> None:
        project = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Project 1",
            object_key="project_1",
        )
        source_type = SourceType(
            id=1, last_updated=date(2026, 1, 1), name="S3", object_key="s3", base_url="s3://geospatial_s3_bucket"
        )

        data_format = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raster",
            object_key="raster",
        )

        data_category = DataCategory(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Category 1",
            object_key="category_1",
            data_category_group=IDModel(
                id=1, last_updated=date(2026, 1, 1), name="Category group 1", object_key="group_1"
            ),
        )

        location = Location(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Location 1",
            object_key="location_1",
            location_type=IDModel(
                id=1,
                last_updated=date(2026, 1, 1),
                name="Location Type 1",
                object_key="location_type_1",
            ),
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        )

        processing_level = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raw",
            object_key="raw",
        )

        layer = Layer(
            id=1,
            name="Layer 1",
            description="Add description here",
            project=project,
            date=None,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            source_type=source_type,
            colour_source_id="colour_raster.tif",
            raw_source_id="greyscale_raster.tif",
            layer_id=None,
            data_format=data_format,
            data_category=data_category,
            legend={
                "type": "range",
                "values": [
                    {
                        "min": {"value": 289.97, "colour": [51, 51, 153]},
                        "max": {"value": 291.61, "colour": [14, 126, 228]},
                    },
                    {
                        "min": {"value": 291.61, "colour": [14, 126, 228]},
                        "max": {"value": 293.25, "colour": [1, 188, 148]},
                    },
                ],
            },
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            bbox=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            processing_level=processing_level,
            location=location,
            field_metadata=None,
            filter_metadata=None,
        )

        expected_source_url = (
            "s3://geospatial_s3_bucket/project=project_1/location_type=location_type_1/location=location_1/"
            "data_category=category_1/processing_level=raw/date=2025-01-01-2026-01-01/colour_raster.tif"
        )

        source_url = layer.get_source_url(source_id="colour_raster.tif")

        assert source_url == expected_source_url

    def test_get_source_url_not_s3_source(self) -> None:
        project = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Project 1",
            object_key="project_1",
        )
        source_type = SourceType(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Metadata API",
            object_key="metadata_api",
            base_url="https://dri-metadata-api.dri.ceh.ac.uk",
        )

        data_format = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raster",
            object_key="raster",
        )

        data_category = DataCategory(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Category 1",
            object_key="category_1",
            data_category_group=IDModel(
                id=1, last_updated=date(2026, 1, 1), name="Category group 1", object_key="group_1"
            ),
        )

        location = Location(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Location 1",
            object_key="location_1",
            location_type=IDModel(
                id=1,
                last_updated=date(2026, 1, 1),
                name="Location Type 1",
                object_key="location_type_1",
            ),
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
        )

        processing_level = IDModel(
            id=1,
            last_updated=date(2026, 1, 1),
            name="Raw",
            object_key="raw",
        )

        layer = Layer(
            id=1,
            name="Layer 1",
            description="Add description here",
            project=project,
            date=None,
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            source_type=source_type,
            colour_source_id=None,
            raw_source_id=(
                "id/network/cosmos?_projection=contains.label,contains.comment,contains.identifier,contains."
                "hasGeometry.*"
            ),
            layer_id="wms",
            data_format=data_format,
            data_category=data_category,
            legend={
                "type": "range",
                "values": [
                    {
                        "min": {"value": 289.97, "colour": [51, 51, 153]},
                        "max": {"value": 291.61, "colour": [14, 126, 228]},
                    },
                    {
                        "min": {"value": 291.61, "colour": [14, 126, 228]},
                        "max": {"value": 293.25, "colour": [1, 188, 148]},
                    },
                ],
            },
            boundary=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            bbox=shapely.from_wkt("POLYGON((0 0,0 1,1 1,1 0,0 0))"),
            processing_level=processing_level,
            location=location,
            field_metadata=None,
            filter_metadata=None,
        )

        expected_source_url = (
            "https://dri-metadata-api.dri.ceh.ac.uk/id/network/cosmos?_projection=contains.label,contains.comment,"
            "contains.identifier,contains.hasGeometry.*"
        )

        source_url = layer.get_source_url(source_id="colour_raster.tif")

        assert source_url == expected_source_url
