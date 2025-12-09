"""Custom TilerFactory with caching, based on https://developmentseed.org/titiler/examples/code/tiler_with_cache/."""

import logging
from dataclasses import dataclass
from typing import Dict, Literal, Type

import rasterio
from fastapi import Depends, Path
from pydantic import Field
from rio_tiler.io import BaseReader, Reader
from rio_tiler.utils import CRS_to_uri
from starlette.responses import Response
from titiler.core.dependencies import BidxExprParams, DatasetParams, DefaultDependency, ImageRenderingParams, TileParams
from titiler.core.factory import TilerFactory as TiTilerFactory
from titiler.core.factory import img_endpoint_params
from titiler.core.resources.enums import ImageType
from typing_extensions import Annotated

from geospatial_api.cache import CachedTiles

logger = logging.getLogger(__name__)


@dataclass
class TilerFactory(TiTilerFactory):
    default_tms = "WebMercatorQuad"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reader: Type[BaseReader] = Reader

    def register_routes(self) -> None:
        """This Method register routes to the router."""

        @self.router.get(r"/tiles/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(r"/tiles/{z}/{x}/{y}@{scale}x.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}.{format}", **img_endpoint_params)
        @self.router.get(r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x", **img_endpoint_params)
        @self.router.get(
            r"/tiles/{tileMatrixSetId}/{z}/{x}/{y}@{scale}x.{format}",
            **img_endpoint_params,
        )
        # Add default cache config dictionary into cached alias.
        # Note: if alias is used, other arguments in cached will be ignored. Add other arguments into default
        # dictionary in setup_cache function.
        @CachedTiles(alias="default")
        def tile(
            z: Annotated[
                int,
                Path(
                    description=(
                        "Identifier (Z) selecting one of the scales defined in the TileMatrixSet and representing the "
                        "scaleDenominator the tile."
                    ),
                ),
            ],
            x: Annotated[
                int,
                Path(
                    description=(
                        "Column (X) index of the tile on the selected TileMatrix. It cannot exceed the MatrixHeight-1 "
                        "for the selected TileMatrix."
                    ),
                ),
            ],
            y: Annotated[
                int,
                Path(
                    description=(
                        "Row (Y) index of the tile on the selected TileMatrix. It cannot exceed the MatrixWidth-1 "
                        "for the selected TileMatrix."
                    ),
                ),
            ],
            tileMatrixSetId: Annotated[
                Literal[tuple(self.supported_tms.list())],
                Path(description="Identifier selecting one of the TileMatrixSetId supported."),
            ],
            scale: Annotated[
                int,
                Field(gt=0, le=4, description="Tile size scale. 1=256x256, 2=512x512..."),
            ] = 1,
            format: Annotated[  # noqa A002
                ImageType,
                Field(
                    description=(
                        "Default will be automatically defined if the output image needs a mask (png) or not (jpeg)."
                    )
                ),
            ] = None,
            src_path: str = Depends(self.path_dependency),
            reader_params: DefaultDependency = Depends(self.reader_dependency),
            tile_params: TileParams = Depends(self.tile_dependency),
            layer_params: BidxExprParams = Depends(self.layer_dependency),
            dataset_params: DatasetParams = Depends(self.dataset_dependency),
            post_process: bool = Depends(self.process_dependency),
            colormap: str = Depends(self.colormap_dependency),
            render_params: ImageRenderingParams = Depends(self.render_dependency),
            env: dict = Depends(self.environment_dependency),
        ) -> Response:
            """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, tms=tms, **reader_params.as_dict()) as src_dst:
                    image = src_dst.tile(
                        x,
                        y,
                        z,
                        tilesize=scale * 256,
                        **tile_params.as_dict(),
                        **layer_params.as_dict(),
                        **dataset_params.as_dict(),
                    )
                    dst_colormap = getattr(src_dst, "colormap", None)

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: Dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)
