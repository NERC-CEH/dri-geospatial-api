import json
from datetime import datetime
from pathlib import Path
from typing import Any

import geojson
import rasterio
import shapely

# DATA_DIR = Path(__file__).parents[2].joinpath("data")
DATA_DIR = Path("/data")

RASTER_TYPE = "raster"
VECTOR_TYPE = "vector"
POINT_RECORD_TYPE = "point_record"

FDRI_PROJECT = "fdri"
DSM_DATA_TYPE = "dsm"
LEGEND_SUFFIX = "_legend.json"
REGION_CATEGORY_NAME = "region"
REGION_CATEGORY_VALUE = "uk"


def main() -> dict[str, Any]:
    build_layer_registry()


def build_layer_registry() -> dict[str, Any]:
    layer_registry = []
    for file_path in DATA_DIR.glob("*.*"):
        layer_data = {
            "name": file_path.stem,
            "project": FDRI_PROJECT,
            "start_date": datetime.now().date(),
            "end_date": datetime.now().date(),
            "s3_key": file_path.name,
            "categories": [{REGION_CATEGORY_NAME: REGION_CATEGORY_VALUE}],
            "data_type": DSM_DATA_TYPE,
        }

        data_format = RASTER_TYPE
        if file_path.suffix == ".tif":
            # Calculate the resolution and fetch the legend information
            ds = rasterio.open(file_path)
            layer_data["resolution"] = ds.get_transform()[1]
            layer_data["bbox"] = shapely.Polygon(
                [
                    [ds.bounds.left, ds.bounds.bottom],
                    [ds.bounds.left, ds.bounds.top],
                    [ds.bounds.right, ds.bounds.top],
                    [ds.bounds.right, ds.bounds.bottom],
                    [ds.bounds.left, ds.bounds.bottom],
                ]
            )
            legend_path = file_path.parent.joinpath(f"{file_path.stem}{LEGEND_SUFFIX}")
            with open(legend_path) as legend_file:
                legend_data = json.load(legend_file)
            layer_data["legend"] = legend_data

        elif file_path.suffix == ".geojson":
            # Read the geojson file, and set the data format to be either point_record or vector depending on the
            # geometry type.

            data_format = VECTOR_TYPE
            with open(str(file_path)) as geojson_file:
                geojson_data = geojson.load(geojson_file)
                if geojson_data.features[0].geometry.type == "Point":
                    data_format = POINT_RECORD_TYPE

        else:
            # Ensure this entry isn't added to the layer registry
            continue

        layer_data["data_format"] = data_format
        layer_data["s3_key"] = file_path.name

        layer_registry.append(layer_data)

    print("Layer registry")
    print(layer_registry)
    return layer_registry


if __name__ == "__main__":
    main()
