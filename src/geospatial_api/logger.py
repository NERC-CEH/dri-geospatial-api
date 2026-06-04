import logging


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "GET /api/healthcheck" not in record.getMessage()
