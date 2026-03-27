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


class AreaName(IDModel):
    area_type: IDModel

    def to_json_response(self) -> dict[str, Any]:
        response = super().to_json_response()
        response["area_type"] = self.area_type.to_json_response()
        return response


class Layer(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    name: str
    project: IDModel
    date: datetime
    source_type: SourceType
    source_id: str
    catalogue_id: Optional[str]
    data_format: IDModel
    data_category: IDModel
    resolution: Optional[float | int]
    legend: Optional[list[dict[str, Any]]]
    boundary: Optional[shapely.Polygon]
    bbox: shapely.Polygon
    centroid: shapely.Point
    processing_level: IDModel
    area_name: AreaName

    def to_json_response(self) -> dict[str, Any]:
        # To save manually declaring the simpler fields, start off with a direct dictionary version of the model.
        # Then modify indiviudal fields to make them suitable for a JSONResponse object
        response = self.__dict__.copy()

        # Convert the start and end dates to iso formatted date strings
        response["date"] = self.date.strftime("%Y-%m-%d")

        # Convert the various sub-models to json
        response["project"] = self.project.to_json_response()
        response["source_type"] = self.source_type.to_json_response()
        response["data_format"] = self.data_format.to_json_response()
        response["data_category"] = self.data_category.to_json_response()
        response["area_name"] = self.area_name.to_json_response()
        response["processing_level"] = self.processing_level.to_json_response()

        # Convert the geometry information to WKT strings. At this point only the bbox and centroid need returning
        del response["boundary"]
        response["bbox"] = self.bbox.wkt
        response["centroid"] = self.centroid.wkt

        # Construct the source_url from the other
        response["source_url"] = self.get_source_url()

        return response

    def get_source_url(self) -> str:
        if self.source_type.object_key.lower() == "s3":
            bucket_keys = (
                f"project={self.project.object_key}/"
                f"area_type={self.area_name.area_type.object_key}/"
                f"area_name={self.area_name.object_key}/"
                f"data_category={self.data_category.object_key}/"
                f"processing_level={self.data_category.object_key}/"
                f"date={self.data_category.object_key}/"
            )

            source_url = f"{self.source_type.base_url}/{bucket_keys}/{self.source_id}"
            return source_url

        # The provided base url may already have the joining /. If this is the case, set the joining character to ""
        join_character = "/"
        if self.source_type.base_url.endswith("/"):
            join_character = ""

        return f"{self.source_type.base_url}{join_character}{source_url}"
