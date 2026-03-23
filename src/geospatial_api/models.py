from datetime import datetime
from typing import Any, Optional

import shapely
from pydantic import BaseModel, ConfigDict


class IDModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    last_updated: datetime
    name: str
    object_key: str

    def to_json_response(self) -> dict[str, Any]:
        response = {"id": self.id, "name": self.name, "object_key": self.object_key}
        return response


class SourceType(IDModel):
    model_config = ConfigDict(extra="ignore")

    base_url: str

    def to_json_response(self) -> dict[str, Any]:
        response = super().to_json_response()
        response["base_url"] = self.base_url
        return response


class Category(IDModel):
    category_type: IDModel

    def to_json_response(self) -> dict[str, Any]:
        response = super().to_json_response()
        response["category_type"] = self.category_type.to_json_response()
        return response


class Layer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    project: IDModel
    start_date: datetime
    end_date: datetime
    source_type: SourceType
    source_id: str
    catalogue_id: Optional[str]
    data_format: IDModel
    data_type: IDModel
    resolution: Optional[float | int]
    legend: Optional[list[dict[str, Any]]]
    boundary: Optional[shapely.Polygon]
    bbox: shapely.Polygon
    centroid: shapely.Point
    primary_category: IDModel
    secondary_category: Optional[IDModel] = None
    tertiary_category: Optional[IDModel] = None

    def to_json_response(self) -> dict[str, Any]:
        # To save manually declaring the simpler fields, start off with a direct dictionary version of the model.
        # Then modify indiviudal fields to make them suitable for a JSONResponse object
        response = self.__dict__.copy()

        # Convert the start and end dates to iso formatted date strings
        response["start_date"] = self.start_date.strftime("%Y-%m-%d")
        response["end_date"] = self.end_date.strftime("%Y-%m-%d")

        # Convert the various sub-models to json
        response["project"] = self.project.to_json_response()
        response["source_type"] = self.source_type.to_json_response()
        response["data_format"] = self.data_format.to_json_response()
        response["data_type"] = self.data_type.to_json_response()
        response['primary_category'] = self.primary_category.to_json_response()
        response['secondary_category'] = self.secondary_category.to_json_response() if self.secondary_category else None
        response['tertiary_category'] = self.tertiary_category.to_json_response() if self.tertiary_category else None

        # Convert the geometry information to WKT strings. At this point only the bbox and centroid need returning
        del response["boundary"]
        response["bbox"] = self.bbox.wkt
        response["centroid"] = self.centroid.wkt

        # Construct the source_url from the other

        return response

    def get_source_url(self) -> str:
        if self.source_type.object_key.lower() == "s3":
            secondary_key = f"/{self.secondary_category.object_key}" if self.secondary_category else ""
            tertiary_key = f"/{self.tertiary_category.object_key}" if self.tertiary_category else ""

            bucket_keys = f"{self.primary_category.object_key}{secondary_key}{tertiary_key}"
            source_url = f"{self.source_type.base_url}/{bucket_keys}/{self.source_id}"
            return source_url

        # The provided base url may already have the joining /. If this is the case, set the joining character to ""
        join_character = "/"
        if self.source_type.base_url.endswith("/"):
            join_character = ""

        return f"{self.source_type.base_url}{join_character}{source_url}"