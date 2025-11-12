import os

import uvicorn

# Find API run environment
local = True
if "api_environment" in os.environ and os.environ["api_environment"] in ["staging", "production"]:
    local = False


def start_server(local: bool) -> None:
    """Start a uvicorn server based on api run environment.

    Args:
        local: whether running locally or in kubernetes.
    """
    if local:
        uvicorn.run(
            "geospatial_api.main:app",
            reload=True,
            reload_includes="*.env",
            log_config="src/geospatial_api/__assets__/log_config.yaml",
            log_level="debug",
        )
    else:
        uvicorn.run(
            "geospatial_api.main:app", log_config="src/geospatial_api/__assets__/log_config.yaml", log_level="debug"
        )


if __name__ == "__main__":
    start_server(local)
