import prometheus_client as prom
from fastapi import FastAPI
from prometheus_client import CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator


class Metrics:
    """Configuring the prometheus metrics for the Geospatial API."""

    def __init__(self, service_name: str) -> None:
        """Initialise custom metrics.

        Args:
            service_name: The service being metricked.
        """
        self.service_name = service_name

    def setup_metrics(self, service: FastAPI) -> None:
        """Setup metrics for FastAPI services.

        Default metrics from fastapi instrumentator are included here.
        Custom metrics are also collected in the routers.

        Args:
            service: The FastAPI service.
        """
        # Start instrumentation and add the default metrics
        instrumentator = Instrumentator(excluded_handlers=["/openapi.json"])
        instrumentator.instrument(service, metric_namespace=self.service_name)

        # Set new registry
        self.registry = CollectorRegistry()

        # Export metrics to port 8080
        prom.start_http_server(8080)
