import prometheus_client as prom
from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator


class Metrics:
    """Configuring the prometheus metrics for the Geospatial API."""

    def setup_metrics(self, service: FastAPI) -> None:
        """Setup metrics for FastAPI services.

        Default metrics from fastapi instrumentator are included here.
        Custom metrics are also collected in the routers.

        Args:
            service: The FastAPI service.
        """
        # Start instrumentation and add the default metrics
        instrumentator = Instrumentator(excluded_handlers=["/openapi.json"])
        instrumentator.instrument(service)

        # Set new registry
        self.registry = CollectorRegistry()

        # Export metrics to port 8080
        prom.start_http_server(8080)
