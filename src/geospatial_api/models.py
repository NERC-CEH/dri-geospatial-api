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
        response = {"id": self.id, "name": self.name, "object_key": self.object_key, "base_url": self.base_url}
        return response


class LayerRegistryItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    project: IDModel
    start_date: datetime
    end_date: datetime
    source_type: SourceType
    source_id: str
    source_url: str
    catalogue_id: Optional[str]
    data_format: IDModel
    data_type: IDModel
    resolution: Optional[float | int]
    legend: Optional[list[dict[str, Any]]]
    boundary: Optional[shapely.Polygon]
    bbox: shapely.Polygon
    centroid: shapely.Point

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

        # Convert the geometry information to WKT strings. At this point only the bbox and centroid need returning
        del response["boundary"]
        response["bbox"] = self.bbox.wkt
        response["centroid"] = self.centroid.wkt

        return response
