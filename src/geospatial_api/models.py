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
    colour_source_id: Optional[str]
    raw_source_id: Optional[str]
    catalogue_id: Optional[str]
    data_format: IDModel
    data_category: IDModel
    legend: Optional[dict[str, Any]]
    boundary: Optional[shapely.Polygon]
    bbox: shapely.Polygon
    processing_level: IDModel
    area_name: AreaName

    def to_json_response(self) -> dict[str, Any]:
        """Convert the Layer model instance to a dictionary able to be easily converted to a JSONResponse object

        Returns:
            Dictionary containing the data to be converted to a JSONResponse object by the api endpoint.

        """
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

        # Convert the geometry information into a series of bounds and the map centroid
        min_x, min_y, max_x, max_y = self.bbox.bounds
        response["bbox"] = {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y}

        response["map_center"] = [self.bbox.centroid.x, self.bbox.centroid.y]

        # Construct the source_url from the other
        response["colour_source_url"] = (
            self.get_source_url(source_id=self.colour_source_id) if self.colour_source_id else None
        )
        response["raw_source_url"] = self.get_source_url(source_id=self.raw_source_id) if self.raw_source_id else None

        # Remove any unneeded keys
        keys_to_remove = ["boundary", "colour_source_id", "raw_source_id"]
        for key in keys_to_remove:
            del response[key]

        return response

    def get_source_url(self, source_id: str) -> str:
        """Construct the source url for the raw or colour source id.

        At present it is assumed that the S3 bucket structure is constant.

        """
        if self.source_type.object_key.lower() == "s3":
            bucket_keys = (
                f"project={self.project.object_key}/"
                f"area_type={self.area_name.area_type.object_key}/"
                f"area_name={self.area_name.object_key}/"
                f"data_category={self.data_category.object_key}/"
                f"processing_level={self.processing_level.object_key}/"
                f"date={self.date.date()}"
            )

            source_url = f"{self.source_type.base_url}/{bucket_keys}/{source_id}"
            return source_url

        # The provided base url may already have the joining /. If this is the case, set the joining character to ""
        join_character = "/"
        if self.source_type.base_url.endswith("/"):
            join_character = ""

        return f"{self.source_type.base_url}{join_character}{source_url}"
