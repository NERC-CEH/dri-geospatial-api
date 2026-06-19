import logging

from driutils.logger import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache import setup_cache
from .config import setup_config
from .metrics import Metrics
from .routers import docs as api_docs
from .routers import healthcheck, layer_management, titiler_main, vector_main
from .routers import main as main_router

logger = logging.getLogger(__name__)

# Setup logging
setup_logging()

# Setup Metadata
config = setup_config()

# Setup the base application
# --------------------------

# Initialise API
app = FastAPI(docs_url=None)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise the cache
app.add_event_handler("startup", setup_cache)

# Setup the API
# ------------------------

# Initialise API
logger.info("Initialising TiTiler API")
api = FastAPI(
    title=config.title,
    description=config.description,
    contact={"name": config.contact_name, "url": config.contact_url},
    docs_url=None,
    openapi_url=None,
)

# metrics
metrics = Metrics(service_name="geospatial_api")
metrics.setup_metrics(service=api)

# state
api.state.config = config

# public routes
api.include_router(healthcheck.public_router)
api.include_router(main_router.public_router)
api.include_router(titiler_main.router, prefix="/maps", tags=["Raster Data"])
api.include_router(vector_main.public_router, tags=["Vector Data"])

# private routes
api.include_router(layer_management.private_router)

# Documentation
api_docs.setup_docs(api)

# Mount services into base application
# ------------------------------------

logger.info("Mounting API into main application")
app.mount("/api", api)
