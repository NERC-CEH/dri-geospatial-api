"""Custom TilerFactory with caching, based on https://developmentseed.org/titiler/examples/code/tiler_with_cache/."""

import logging
from dataclasses import dataclass
from typing import Callable, Literal, Type

import rasterio
from fastapi import Depends, HTTPException, Path
from pydantic import Field
from rio_tiler.errors import TileOutsideBounds
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
            post_process: Callable = Depends(self.process_dependency),
            colormap: str = Depends(self.colormap_dependency),
            render_params: ImageRenderingParams = Depends(self.render_dependency),
            env: dict = Depends(self.environment_dependency),
        ) -> Response:
            """
            Create a single map tile from the provided dataset.

            Args:
                z: The zoom level of the tile to be returned. For example for WebMercatorQuad, a zoom level of 24 would
                    correspond to tile covering roughly a 2x2m square.
                x: index on the X axis of the tile to be returned. This value should align to the selected TileMatrix
                    (e.g. WebMercatorQuad) and cannot exceed the MatrixHeight-1.
                x: index on the Y axis of the tile to be returned. This value should align to the selected TileMatrix
                    (e.g. WebMercatorQuad) and cannot exceed the MatrixWidth-1.
                tileMatrixSetId: Name of the TileMatrixSetId to use.
                scale:  Tile size scale, where 1=256x256, 2=512x512 etc. Defaults to 0.
                format: The format of the image, e.g. PNG. This will be automatically determined from the source path
                    if no value is provided.
                src_path: The path to the raster to extract a tile from. This can be a local file path or an S3 url.
                reader_params: Paramsters to pass through to the tile reader.
                tile_params: Tile specific parameters to use when creating the tile. For example whether to buffer the
                    boundary of the tile, and if so by what distance (m).
                layer_params: Raster band specific parameters to use when creating the tile.
                dataset_params: Dataset specific parameters to use when creating the tile. For example the nodata value.
                post_process: Optional function to apply to the generated tile after it has been created.
                colormap: Name of the colourmap to apply (if relevant). For example "viridis".
                render_params: Image rendering parameters, for example whether to add a mask to the output tile.
                env: Dictionary of any environment variables to use during processing.

            Returns:
                Response object containing the tile image bytes alongside headers detailing the tile boundaries, CRS,
                    image file type and size.

            """
            # """Create map tile from a dataset."""
            tms = self.supported_tms.get(tileMatrixSetId)
            with rasterio.Env(**env):
                logger.info(f"opening data with reader: {self.reader}")
                with self.reader(src_path, tms=tms, **reader_params.as_dict()) as src_dst:
                    try:
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
                    except TileOutsideBounds:
                        raise HTTPException(status_code=500, detail="Requested tile is outside of the raster bounds.")

            if post_process:
                image = post_process(image)

            content, media_type = self.render_func(
                image,
                output_format=format,
                colormap=colormap or dst_colormap,
                **render_params.as_dict(),
            )

            headers: dict[str, str] = {}
            if image.bounds is not None:
                headers["Content-Bbox"] = ",".join(map(str, image.bounds))
            if uri := CRS_to_uri(image.crs):
                headers["Content-Crs"] = f"<{uri}>"

            return Response(content, media_type=media_type, headers=headers)
