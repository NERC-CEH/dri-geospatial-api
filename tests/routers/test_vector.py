from pathlib import Path
from typing import Any
from unittest.mock import patch

import geojson
import pytest
from fastapi.testclient import TestClient
from httpx import Request, Response

import geospatial_api.models as pydantic_models
from geospatial_api.main import app
from geospatial_api.services.rds.db import LayerRegistryInterface

client = TestClient(app)


@pytest.fixture()
def expected_geojson(data_dir: Path) -> dict[str, Any]:
    geojson_path = data_dir.joinpath("cosmos_sites.geojson")
    with open(geojson_path) as geojson_file:
        geojson_data = geojson.load(geojson_file)

    return geojson_data


class TestVector:
    def test_vector_from_s3(self, expected_geojson: dict[str, Any]) -> None:
        """Test the vector endpoint returns valid geojson from s3."""
        response = client.get(
            "private/api/vector?url=s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=national/location=uk/"
            "data_category=soil_moisture/processing_level=processed/date=2026-03-20-2026-05-01/cosmos_sites.geojson"
        )
        assert response.status_code == 200
        assert response.json() == expected_geojson

    def test_vector_from_file_url(self, data_dir: Path, expected_geojson: dict[str, Any]) -> None:
        """Test the vector endpoint returns valid geojson from a file:// url."""
        geojson_path = data_dir.joinpath("cosmos_sites.geojson")
        response = client.get(f"private/api/vector?url=file:///{geojson_path}")
        assert response.status_code == 200
        assert response.json() == expected_geojson

    def test_vector_from_metadata_api(self) -> None:
        response_json = {
            "meta": {
                "@id": (
                    "http://fdri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,"
                    "contains.identifier,contains.hasGeometry.*"
                ),
                "publisher": "UK Centre for Ecology & Hydrology",
                "license": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "licenseName": "OGL 3",
                "comment": "",
                "version": "1.0.0",
                "hasFormat": [
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.csv?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.geojson?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.ttl?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.rdf?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.html?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                ],
            },
            "items": [
                {
                    "@id": "http://fdri.ceh.ac.uk/id/network/cosmos",
                    "contains": [
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn",
                            "label": ["Waddesdon"],
                            "comment": [
                                (
                                    "This is a gentle sloping grassland site with deep clay/loam soil. It is close to "
                                    "Aylesbury in Buckinghamshire and within the estate of Waddesdon Manor. Two eddy "
                                    "covariance flux monitoring sites are located nearby."
                                )
                            ],
                            "identifier": ["WADDN"],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn#geo-eastings",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(472548.0 216170.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn#geo-latlong",
                                    "asWKT": "POINT(-0.948405 51.839436)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                        },
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln",
                            "label": ["Hollin Hill"],
                            "comment": [
                                (
                                    "The site at Hollin Hill is on a steep south facing slope in the Howardian Hills "
                                    "to the north-east of York. The steepness means that it departs from the ideal "
                                    "requirements for a COSMOS-UK site, but the site is interesting as a landslide "
                                    "observatory operated by the British Geological Survey. It is a grassland site on "
                                    "which sheep graze."
                                )
                            ],
                            "identifier": ["HOLLN"],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln#geo-latlong",
                                    "asWKT": "POINT(-0.959477 54.110665)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln#geo-eastings",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(468123.0 468809.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        with (
            patch("requests.Session.get") as mock_get,
            patch.object(LayerRegistryInterface, "get_single_layer") as mock_get_layer,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json=response_json, request=mock_request)
            mock_get.return_value = mock_response

            mock_get_layer.return_value = pydantic_models.Layer.model_construct(
                source_type=pydantic_models.SourceType.model_construct(object_key="metadata_api"),
                field_metadata=[
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "comment",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [
                            {"key": "hasGeometry", "type": "wkt_list", "index": None},
                        ],
                        "data_type": "string",
                    },
                ],
                filter_metadata=None,
                resource_metadata=None,
            )

            expected_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-0.948405, 51.839436]},
                        "properties": {
                            "name": "Waddesdon",
                            "comment": (
                                "This is a gentle sloping grassland site with deep clay/loam soil. It is close to "
                                "Aylesbury in Buckinghamshire and within the estate of Waddesdon Manor. Two eddy "
                                "covariance flux monitoring sites are located nearby."
                            ),
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-0.959477, 54.110665]},
                        "properties": {
                            "name": "Hollin Hill",
                            "comment": (
                                "The site at Hollin Hill is on a steep south facing slope in the Howardian Hills to "
                                "the north-east of York. The steepness means that it departs from the ideal "
                                "requirements for a COSMOS-UK site, but the site is interesting as a landslide "
                                "observatory operated by the British Geological Survey. It is a grassland site on "
                                "which sheep graze."
                            ),
                        },
                    },
                ],
            }

            response = client.get(
                "private/api/vector?url=https://dri-metadata-api.dri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*&layer_id=1"
            )

            assert response.status_code == 200
            assert response.json() == expected_json

    def test_vector_from_metadata_api_missing_fields(self) -> None:
        response_json = {
            "meta": {
                "@id": (
                    "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.json?_projection=contains.label,"
                    "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                    "contains.altitude"
                ),
                "publisher": "UK Centre for Ecology & Hydrology",
                "license": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "licenseName": "OGL 3",
                "comment": "",
                "version": "1.0.0",
                "hasFormat": [
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.rdf?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.csv?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.geojson?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.json?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.ttl?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.html?_projection=contains.label,"
                        "contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,"
                        "contains.altitude"
                    ),
                ],
            },
            "items": [
                {
                    "@id": "http://fdri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period",
                    "contains": [
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_sev-7",
                            "label": ["Hore D2X"],
                            "comment": [
                                (
                                    "Installed as part of a network of 39 gauges for an Institute of Hydrology Study "
                                    "on domain theory. The characters D2X correspond to the altitude, slope and aspect "
                                    "of the gauge location respectively. The gauge is a ground level gauge."
                                )
                            ],
                            "identifier": ["internal_database_id|507", "gauge_code|sev-7"],
                            "hasGeometry": [
                                {
                                    "@id": (
                                        "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_sev-7#"
                                        "geometry.eastingnorthing"
                                    ),
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(281960.0 288340.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": (
                                        "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_sev-7#geometry.latlong"
                                    ),
                                    "asWKT": "POINT(-3.739537 52.480178)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                            "operatingPeriod": {
                                "@id": "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_sev-7#operating-period",
                                "@type": [{"@id": "http://purl.org/dc/terms/PeriodOfTime"}],
                                "startDate": "1969-01-17",
                            },
                            "altitude": 668,
                        },
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_hafod-cadwgan",
                            "label": ["Hafod Cadwgan"],
                            "identifier": ["gauge_code|hafod-cadwgan", "internal_database_id|577"],
                            "hasGeometry": [
                                {
                                    "@id": (
                                        "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_hafod-cadwgan#"
                                        "geometry.eastingnorthing"
                                    ),
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(285900.0 290550.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": (
                                        "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_hafod-cadwgan#"
                                        "geometry.latlong"
                                    ),
                                    "asWKT": "POINT(-3.68231 52.50088)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                            "operatingPeriod": {
                                "@id": (
                                    "http://fdri.ceh.ac.uk/id/site/plynlimon-pre-fdri-period_hafod-cadwgan#"
                                    "operating-period"
                                ),
                                "@type": [{"@id": "http://purl.org/dc/terms/PeriodOfTime"}],
                                "startDate": "1969-01-17",
                            },
                            "altitude": 366,
                        },
                    ],
                }
            ],
        }

        with (
            patch("requests.Session.get") as mock_get,
            patch.object(LayerRegistryInterface, "get_single_layer") as mock_get_layer,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json=response_json, request=mock_request)
            mock_get.return_value = mock_response

            mock_get_layer.return_value = pydantic_models.Layer.model_construct(
                source_type=pydantic_models.SourceType.model_construct(object_key="metadata_api"),
                field_metadata=[
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Altitude",
                        "key": "altitude",
                        "field_keys": [{"key": "altitude", "type": "value"}],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Start Date",
                        "key": "start_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "startDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "End date",
                        "key": "end_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "endDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                filter_metadata=None,
                resource_metadata=None,
            )

            expected_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-3.739537, 52.480178]},
                        "properties": {
                            "name": "Hore D2X",
                            "description": (
                                "Installed as part of a network of 39 gauges for an Institute of Hydrology Study on "
                                "domain theory. The characters D2X correspond to the altitude, slope and aspect of the "
                                "gauge location respectively. The gauge is a ground level gauge."
                            ),
                            "altitude": 668,
                            "start_date": "1969-01-17",
                            "end_date": None,
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-3.68231, 52.50088]},
                        "properties": {
                            "name": "Hafod Cadwgan",
                            "description": None,
                            "altitude": 366,
                            "start_date": "1969-01-17",
                            "end_date": None,
                        },
                    },
                ],
            }

            response = client.get(
                "private/api/vector?url=https://dri-metadata-api.dri.ceh.ac.uk/id/network/plynlimon-pre-fdri-period.json?"
                "_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*&layer_id=1"
            )

            assert response.status_code == 200
            assert response.json() == expected_json

    def test_vector_from_metadata_api_apply_filtering(self) -> None:
        response_json = {
            "meta": {},
            "items": [
                {
                    "@id": "http://fdri.ceh.ac.uk/id/network/ea-flow",
                    "contains": [
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001",
                            "label": ["Claypole"],
                            "hasAnnotation": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001#annotation-isChess-0",
                                    "property": {"@id": "http://fdri.ceh.ac.uk/ref/common/annotation/isChess"},
                                    "hasValue": {
                                        "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001#annotation-isChess-0-value",
                                        "value": [False],
                                    },
                                    "@type": [{"@id": "http://fdri.ceh.ac.uk/vocab/metadata/Annotation"}],
                                }
                            ],
                            "identifier": [
                                "nrfaStationID|30001",
                                "notation|6dd5d77f-6994-40fe-be0e-815f7febde94",
                                "RLOIid|6057",
                                "wiskiID|030001",
                            ],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001#geometry.latlong",
                                    "asWKT": "POINT(-0.746155 53.02231)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001#geometry.eastingnorthing",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(484201.0 347959.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                            "operatingPeriod": {
                                "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_030001#operating-period",
                                "@type": [{"@id": "http://purl.org/dc/terms/PeriodOfTime"}],
                                "startDate": "1959-05-01",
                            },
                        },
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th",
                            "label": ["Denham Lodge Main"],
                            "hasAnnotation": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th#annotation-isChess-0",
                                    "property": {"@id": "http://fdri.ceh.ac.uk/ref/common/annotation/isChess"},
                                    "hasValue": {
                                        "@id": (
                                            "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th#annotation-isChess-0-value"
                                        ),
                                        "value": [True],
                                    },
                                    "@type": [{"@id": "http://fdri.ceh.ac.uk/vocab/metadata/Annotation"}],
                                }
                            ],
                            "identifier": [
                                "notation|0ee042cb-d2b3-497b-9305-2ac0a8960696",
                                "wiskiID|2879_w1TH",
                                "RLOIid|7407",
                                "stationReference|2879_w1TH",
                            ],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th#geometry.latlong",
                                    "asWKT": "POINT(-0.49112 51.567599)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th#geometry.eastingnorthing",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(504677.0 186492.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                            "operatingPeriod": {
                                "@id": "http://fdri.ceh.ac.uk/id/site/ea-flow_2879_w1th#operating-period",
                                "@type": [{"@id": "http://purl.org/dc/terms/PeriodOfTime"}],
                                "startDate": "1986-11-01",
                            },
                        },
                    ],
                },
            ],
        }

        with (
            patch("requests.Session.get") as mock_get,
            patch.object(LayerRegistryInterface, "get_single_layer") as mock_get_layer,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json=response_json, request=mock_request)
            mock_get.return_value = mock_response

            mock_get_layer.return_value = pydantic_models.Layer.model_construct(
                source_type=pydantic_models.SourceType.model_construct(object_key="metadata_api"),
                field_metadata=[
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Altitude",
                        "key": "altitude",
                        "field_keys": [{"key": "altitude", "type": "value"}],
                        "data_type": "float",
                    },
                    {
                        "display_label": "Start Date",
                        "key": "start_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "startDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "End date",
                        "key": "end_date",
                        "field_keys": [
                            {"key": "operatingPeriod", "type": "value"},
                            {"key": "endDate", "type": "value"},
                        ],
                        "data_type": "date",
                    },
                    {
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [{"key": "hasGeometry", "type": "wkt_list", "index": None}],
                        "data_type": "string",
                    },
                ],
                filter_metadata=[
                    {
                        "type": "list",
                        "list_field": "hasAnnotation",
                        "id_field_keys": [{"key": "property", "type": "value"}, {"key": "@id", "type": "value"}],
                        "value_field_keys": [
                            {"key": "hasValue", "type": "value"},
                            {"key": "value", "type": "list", "index": 0},
                        ],
                        "expected_id": "http://fdri.ceh.ac.uk/ref/common/annotation/isChess",
                        "expected_value": True,
                    }
                ],
                resource_metadata=None,
            )

            expected_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-0.49112, 51.567599]},
                        "properties": {
                            "name": "Denham Lodge Main",
                            "description": None,
                            "altitude": None,
                            "start_date": "1986-11-01",
                            "end_date": None,
                        },
                    }
                ],
            }
            response = client.get(
                "private/api/vector?url=https://dri-metadata-api.staging.dri.ceh.ac.uk/id/network/ea-flow.json?_view=extended&_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*,contains.operatingPeriod.*,contains.altitude,contains.hasAnnotation.*&_withView&layer_id=1"
            )

            assert response.status_code == 200
            assert response.json() == expected_json

    def test_vector_from_metadata_api_resource_metadata_processing(self) -> None:
        response_json = {
            "meta": {
                "@id": (
                    "http://fdri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,"
                    "contains.identifier,contains.hasGeometry.*"
                ),
                "publisher": "UK Centre for Ecology & Hydrology",
                "license": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "licenseName": "OGL 3",
                "comment": "",
                "version": "1.0.0",
                "hasFormat": [
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.csv?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.geojson?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.ttl?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.rdf?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                    (
                        "http://fdri.ceh.ac.uk/id/network/cosmos.html?_projection=contains.label,contains.comment,"
                        "contains.identifier,contains.hasGeometry.*"
                    ),
                ],
            },
            "items": [
                {
                    "@id": "http://fdri.ceh.ac.uk/id/network/cosmos",
                    "contains": [
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn",
                            "label": ["Waddesdon"],
                            "comment": [
                                (
                                    "This is a gentle sloping grassland site with deep clay/loam soil. It is close to "
                                    "Aylesbury in Buckinghamshire and within the estate of Waddesdon Manor. Two eddy "
                                    "covariance flux monitoring sites are located nearby."
                                )
                            ],
                            "identifier": ["WADDN"],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn#geo-eastings",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(472548.0 216170.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn#geo-latlong",
                                    "asWKT": "POINT(-0.948405 51.839436)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                        },
                        {
                            "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln",
                            "label": ["Hollin Hill"],
                            "comment": [
                                (
                                    "The site at Hollin Hill is on a steep south facing slope in the Howardian Hills "
                                    "to the north-east of York. The steepness means that it departs from the ideal "
                                    "requirements for a COSMOS-UK site, but the site is interesting as a landslide "
                                    "observatory operated by the British Geological Survey. It is a grassland site on "
                                    "which sheep graze."
                                )
                            ],
                            "identifier": ["HOLLN"],
                            "hasGeometry": [
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln#geo-latlong",
                                    "asWKT": "POINT(-0.959477 54.110665)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln#geo-eastings",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(468123.0 468809.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                            ],
                        },
                    ],
                }
            ],
        }

        with (
            patch("requests.Session.get") as mock_get,
            patch.object(LayerRegistryInterface, "get_single_layer") as mock_get_layer,
        ):
            mock_request = Request(method="get", url="http://test_url.com")
            mock_response = Response(200, json=response_json, request=mock_request)
            mock_get.return_value = mock_response

            mock_get_layer.return_value = pydantic_models.Layer.model_construct(
                source_type=pydantic_models.SourceType.model_construct(object_key="metadata_api"),
                field_metadata=[
                    {
                        "display_label": "Name",
                        "key": "name",
                        "field_keys": [{"key": "label", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "ID",
                        "key": "id",
                        "field_keys": [{"key": "identifier", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Description",
                        "key": "description",
                        "field_keys": [{"key": "comment", "type": "list", "index": 0}],
                        "data_type": "string",
                    },
                    {
                        "display_label": "Location",
                        "key": "geometry",
                        "field_keys": [
                            {"key": "hasGeometry", "type": "wkt_list", "index": None},
                        ],
                        "data_type": "string",
                    },
                ],
                filter_metadata=None,
                resource_metadata=[
                    {
                        "level": "layer",
                        "url": "https://catalogue.ceh.ac.uk/",
                        "url_mapping": {},
                        "label": "EIDC catalogue",
                    },
                    {
                        "level": "feature",
                        "url": "https://dri-ui.staging.dri.ceh.ac.uk/fdri/timeseries?network=cosmos&site={site_id}",
                        "url_mapping": {"site_id": "id"},
                        "label": "timeseries data",
                    },
                ],
            )

            expected_json = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-0.948405, 51.839436]},
                        "properties": {
                            "name": "Waddesdon",
                            "id": "WADDN",
                            "description": (
                                "This is a gentle sloping grassland site with deep clay/loam soil. It is close to "
                                "Aylesbury in Buckinghamshire and within the estate of Waddesdon Manor. Two eddy "
                                "covariance flux monitoring sites are located nearby."
                            ),
                            "urls": [
                                {
                                    "label": "timeseries data",
                                    "url": "https://dri-ui.staging.dri.ceh.ac.uk/fdri/timeseries?network=cosmos&site=WADDN",
                                }
                            ],
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [-0.959477, 54.110665]},
                        "properties": {
                            "name": "Hollin Hill",
                            "id": "HOLLN",
                            "description": (
                                "The site at Hollin Hill is on a steep south facing slope in the Howardian Hills to "
                                "the north-east of York. The steepness means that it departs from the ideal "
                                "requirements for a COSMOS-UK site, but the site is interesting as a landslide "
                                "observatory operated by the British Geological Survey. It is a grassland site on "
                                "which sheep graze."
                            ),
                            "urls": [
                                {
                                    "label": "timeseries data",
                                    "url": "https://dri-ui.staging.dri.ceh.ac.uk/fdri/timeseries?network=cosmos&site=HOLLN",
                                }
                            ],
                        },
                    },
                ],
            }

            response = client.get(
                "private/api/vector?url=https://dri-metadata-api.dri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*&layer_id=1"
            )

            assert response.status_code == 200
            assert response.json() == expected_json
