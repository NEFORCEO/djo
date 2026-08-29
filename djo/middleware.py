from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed, JsonResponse

from .config import config, get_gate, is_enabled
from .generator import generate_openapi_schema
from .swagger import get_swagger_html

_SAFE_METHODS = ("GET", "HEAD")


def _normalize(path: str) -> str:
    """`/docs/` and `docs` both normalize to `/docs` for an exact comparison."""
    return "/" + path.strip("/")


class DjangoAPIMiddleware:
    """
    Serves `/docs` and `/openapi.json` ahead of normal URL resolution.

    Installed automatically by `DjangoAPIConfig.ready()` — that's what
    lets the whole package work from a single `INSTALLED_APPS` entry
    with no urls.py changes. Override the paths via a `DJO` dict
    in settings.py, e.g. `DJO = {"DOCS_URL": "/api/docs"}`.

    Both endpoints are gated: they only respond when `is_enabled()` is true
    (defaults to `settings.DEBUG`), only to safe HTTP methods, and only when
    an optional `DJO["GATE"]` callback allows the request. Any other case
    falls through untouched, so nothing about the API is exposed.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        cfg = config()
        self.docs_url = _normalize(cfg.get("DOCS_URL", "/docs"))
        self.openapi_url = _normalize(cfg.get("OPENAPI_URL", "/openapi.json"))

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = _normalize(request.path)

        if path == self.docs_url:
            return self._serve(request, self._docs)
        if path == self.openapi_url:
            return self._serve(request, self._openapi)
        return self.get_response(request)

    def _serve(self, request: HttpRequest, handler: Callable[[HttpRequest], HttpResponse]) -> HttpResponse:
        if not is_enabled():
            return self.get_response(request)
        if request.method not in _SAFE_METHODS:
            return HttpResponseNotAllowed(_SAFE_METHODS)
        gate = get_gate()
        if gate is not None and not gate(request):
            return self.get_response(request)
        return handler(request)

    def _docs(self, request: HttpRequest) -> HttpResponse:
        html = get_swagger_html(openapi_url=self.openapi_url)
        return HttpResponse(html, content_type="text/html")

    def _openapi(self, request: HttpRequest) -> HttpResponse:
        schema = generate_openapi_schema()
        return JsonResponse(schema, json_dumps_params={"indent": 2})
