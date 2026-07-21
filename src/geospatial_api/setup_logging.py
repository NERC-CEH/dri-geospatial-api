import inspect
import logging
import os
import sys
from collections.abc import Awaitable, Callable

from driutils.json_logger import json_formatter, log_extras  # noqa: F401
from fastapi import FastAPI, Request, Response
from loguru import logger


class _InterceptHandler(logging.Handler):
    """Bridges stdlib logging to loguru.

    Uvicorn uses Python's stdlib logging internally. This handler intercepts those
    records and forwards them to loguru so all logs are formatted and filtered
    consistently, regardless of whether they originated from the app or uvicorn.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Forward a stdlib log record to loguru.

        Translates the stdlib level name to a loguru level.
        Falls back to the numeric level if loguru doesn't recognise the name.

        A fixed depth doesn't work here: stdlib methods like `Logger.exception`
        wrap `Logger.error` and add an extra stack frame, so the depth needed to
        reach the true call site varies by which method was called. Walk up from
        this frame, past the stdlib logging internals, to find it instead.

        Args:
            record: the stdlib log record to forward.
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _local_formatter(record: dict) -> str:
    """Human-readable log format for local development.

    The standard JSON format is machine-readable but hard to follow locally,
    so this formatter is used when api_environment is not set.

    Args:
        record: the loguru record object.

    Returns:
        A log string
    """
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    parts = [
        f"time={timestamp}",
        f"level={record['level'].name}",
        f"thread={record['thread'].id}",
        f"loc={record['name']}:{record['line']}",
    ]
    for key, value in record["extra"].items():
        parts.append(f"{key}={value}")
    parts.append(f"message={record['message']}")
    return (" ".join(parts) + "\n").replace("{", "{{").replace("}", "}}")


def ignore_healthcheck(record: dict) -> bool:
    """Ignore logging the healthcheck request as creates too much unneeded noise."""
    return "GET /api/healthcheck" not in record["message"]


def setup_logger(service_name: str) -> None:
    """Configure loguru for the service based on the run environment.

    Uses human-readable logs locally and structured JSON in staging/production.
    Also intercepts uvicorn's stdlib logging to route through loguru.

    Args:
        service_name: the name of the service
    """
    is_local = "api_environment" not in os.environ

    def _json_formatter(record: dict) -> str:
        return json_formatter(record, service_name=service_name)

    formatter = _local_formatter if is_local else _json_formatter

    logger.remove()
    logger.add(sys.stderr, format=formatter, colorize=False, backtrace=False, filter=ignore_healthcheck)  # type: ignore[arg-type]

    _handler = _InterceptHandler()

    for _name in ("uvicorn", "uvicorn.error"):
        _uv_logger = logging.getLogger(_name)
        _uv_logger.handlers = [_handler]
        _uv_logger.propagate = False

    logging.getLogger("uvicorn.access").disabled = True


def setup_request_middleware(app: FastAPI) -> None:
    """Register request logging middleware on the FastAPI app.

    Collect request details for each http call. Store the status code
    if an error has occurred.

    Args:
        app: The FastAPI application to register the middleware on.
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Ignore healthcheck request
        if request.url.path == "/api/healthcheck":
            return await call_next(request)

        # Bind path and method onto the loguru context so any log calls within the handler inherit them
        with logger.contextualize(api_path=request.url.path, api_method=request.method):
            response = await call_next(request)

        # Emit a single structured access log entry once the response status code is available
        with log_extras(
            {"api_path": request.url.path, "api_method": request.method, "api_status_code": str(response.status_code)}
        ):
            full_path = f"{request.url.path}?{request.url.query}" if request.url.query else request.url.path
            log_message = f"{request.method} {full_path} {response.status_code}"
            if response.status_code >= 400:
                logger.error(log_message)
            else:
                logger.info(log_message)

        return response
