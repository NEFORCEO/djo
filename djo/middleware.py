from __future__ import annotations

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from .generator import generate_openapi_schema
from .swagger import get_swagger_html


class DjangoAPIMiddleware:
    """
    Serves `/docs` and `/openapi.json` ahead of normal URL resolution.

    Installed automatically by `DjangoAPIConfig.ready()` — that's what
    lets the whole package work from a single `INSTALLED_APPS` entry
    with no urls.py changes. Override the paths via a `DJO` dict
    in settings.py, e.g. `DJO = {"DOCS_URL": "/api/docs"}`.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        config = getattr(settings, "DJO", {})
        self.docs_url = config.get("DOCS_URL", "/docs")
        self.openapi_url = config.get("OPENAPI_URL", "/openapi.json")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path.rstrip("/") or "/"

        if path == self.docs_url:
            html = get_swagger_html(openapi_url=self.openapi_url)
            return HttpResponse(html, content_type="text/html")

        if path == self.openapi_url:
            schema = generate_openapi_schema()
            return JsonResponse(schema, json_dumps_params={"indent": 2})

        return self.get_response(request)
