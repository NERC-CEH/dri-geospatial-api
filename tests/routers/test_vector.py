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
            "/api/vector?url=s3://ukceh-fdri-staging-geospatial/project=fdri/location_type=national/location=uk/"
            "data_category=soil_moisture/processing_level=processed/date=2026-03-20-2026-05-01/cosmos_sites.geojson"
        )
        assert response.status_code == 200
        assert response.json() == expected_geojson

    def test_vector_from_file_url(self, data_dir: Path, expected_geojson: dict[str, Any]) -> None:
        """Test the vector endpoint returns valid geojson from a file:// url."""
        geojson_path = data_dir.joinpath("cosmos_sites.geojson")
        response = client.get(f"/api/vector?url=file:///{geojson_path}")
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
                                        "POINT(472548.0, 216170.0)"
                                    ),
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-waddn#geo-latlong",
                                    "asWKT": "POINT(-0.948405, 51.839436)",
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
                                    "asWKT": "POINT(-0.959477, 54.110665)",
                                    "@type": [{"@id": "http://www.opengis.net/ont/geosparql#Geometry"}],
                                },
                                {
                                    "@id": "http://fdri.ceh.ac.uk/id/site/cosmos-holln#geo-eastings",
                                    "asWKT": (
                                        "\u003chttp://www.opengis.net/def/crs/EPSG/0/27700\u003e "
                                        "POINT(468123.0, 468809.0)"
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
                "/api/vector?url=https://dri-metadata-api.dri.ceh.ac.uk/id/network/cosmos.json?_projection=contains.label,contains.comment,contains.identifier,contains.hasGeometry.*&layer_id=1"
            )

            assert response.status_code == 200
            assert response.json() == expected_json
