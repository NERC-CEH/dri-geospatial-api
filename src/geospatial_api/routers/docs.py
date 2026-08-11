from typing import Any

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse


def get_api_root(request: Request) -> str:
    return request.scope.get("root_path", "")


def setup_docs(app: FastAPI, include_private: bool) -> None:
    """Custom docs setup selecting which routes appear in the OpenAPI schema.

    Each mount-driven tree has a fixed schema: ``include_private`` is set once when
    the tree is built in ``build_api``.

    Args:
        app: The FastAPI application to register the routes on.
        include_private: Whether Private-tagged routes appear in the schema.
    """

    @app.get("/docs", include_in_schema=False)
    def docs(request: Request) -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=f"{get_api_root(request)}/openapi.json", title=app.title)

    @app.get("/openapi.json", include_in_schema=False)
    def openapi(request: Request) -> dict[str, Any]:
        routes = app.routes if include_private else [r for r in app.routes if "Private" not in getattr(r, "tags", [])]

        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            contact=app.contact,
            routes=routes,
            servers=[{"url": get_api_root(request)}],
        )
