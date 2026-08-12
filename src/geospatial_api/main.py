from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .cache import setup_cache
from .config import setup_config
from .metrics import Metrics
from .routers import docs as api_docs
from .routers import healthcheck, layer_management, titiler_main, vector_main
from .routers import main as api_root
from .setup_logging import setup_logger, setup_request_middleware

# Setup config
config = setup_config()

# Setup logging
setup_logger(service_name=config.service_name)

# Setup the base application
# --------------------------

# Initialise API
app = FastAPI(docs_url=None)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to log request details
setup_request_middleware(app)

# Initialise the cache
app.add_event_handler("startup", setup_cache)

# Setup the API
# ------------------------


def build_api(access: str) -> FastAPI:
    """Construct a sub-application whose access is driven by its mount point.

    - ``"public"``  -> always the limited/public view (mounted at ``/public/api``).
    - ``"private"`` -> always the full view plus privileged operations
      (mounted at ``/private/api``).

    Args:
        access: The fixed access mode for the tree, ``"public"`` or ``"private"``.

    Returns:
        The configured api FastAPI sub-application.
    """
    api = FastAPI(
        title=config.title,
        description=config.description,
        contact={"name": config.contact_name, "url": config.contact_url},
        docs_url=None,
        openapi_url=None,
    )
    api.state.config = config
    # Fix the view per tree: the private tree serves the full view, the public tree the
    # limited view. Read back by the ``serves_private_view`` dependency.
    api.state.serves_private_view = access == "private"

    api.include_router(healthcheck.router)
    api.include_router(api_root.router)
    api.include_router(titiler_main.router, prefix="/maps", tags=["Raster Data"])
    api.include_router(vector_main.router, tags=["Vector Data"])

    if access != "public":
        api.include_router(layer_management.router)

    api_docs.setup_docs(api, include_private=access != "public")
    return api


# Initialise API
logger.info("Initialising v1 API")
public_api = build_api("public")
private_api = build_api("private")

# Mount services into base application
# ------------------------------------

logger.info("Mounting API into main application")
app.mount("/public/api/", public_api)
app.mount("/private/api/", private_api)

# Instrument the root application so every mounted sub-application is covered
metrics = Metrics()
metrics.setup_metrics(service=app)
