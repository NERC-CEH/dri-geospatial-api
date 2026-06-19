from typing import Any

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from geospatial_api.utils.ip_whitelisting import check_ip_address_is_whitelisted

PRIVATE_ROUTER_TAGS = {"Layer Management"}


def get_api_root(request: Request) -> str:
    return request.scope.get("root_path", "")


def setup_docs(app: FastAPI) -> None:
    """Custom docs setup based on whether the user has public or private access
    to the API.

    Whitelisted IPs see the full schema including Private-tagged endpoints;
    all other IPs see only public endpoints.

    Args:
        app: The FastAPI application to register the routes on.
    """

    @app.get("/docs", include_in_schema=False)
    def docs(request: Request) -> HTMLResponse:
        return get_swagger_ui_html(openapi_url=f"{get_api_root(request)}/openapi.json", title=app.title)

    @app.get("/openapi.json", include_in_schema=False)
    def openapi(request: Request) -> dict[str, Any]:
        # routes = [r for r in app.routes if PRIVATE_ROUTER_TAGS not in getattr(r, "tags", [])]
        routes = [
            r for r in app.routes if any([item for item in PRIVATE_ROUTER_TAGS if item not in getattr(r, "tags", [])])
        ]
        if check_ip_address_is_whitelisted(request):
            routes = app.routes

        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            contact=app.contact,
            routes=routes,
            servers=[{"url": get_api_root(request)}],
        )
