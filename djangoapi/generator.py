from __future__ import annotations

import inspect
from typing import Any

from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import RoutePattern, URLPattern, URLResolver

from .types import (
    ANGLE_PARAM_RE,
    BODY_MARKERS,
    CONVERTER_SCHEMAS,
    FIELD_ACCESS_RE,
    HTTP_METHOD_NAMES,
    SLASH_RUN_RE,
)


def _route_string(pattern: Any) -> str:
    """Best-effort raw route string for a `path()` or `re_path()` pattern."""
    route = getattr(pattern, "_route", None)
    if route is not None:
        return str(route)
    regex = getattr(pattern, "_regex", None)
    if regex is not None:
        return str(regex).lstrip("^").rstrip("$")
    return str(pattern)


def _path_parameters(pattern: Any) -> list[dict[str, Any]]:
    """OpenAPI path parameters inferred from `path()` converters (empty for `re_path()`)."""
    if not isinstance(pattern, RoutePattern):
        return []
    parameters = []
    for name, converter in pattern.converters.items():
        schema = CONVERTER_SCHEMAS.get(type(converter).__name__, {"type": "string"})
        parameters.append({"name": name, "in": "path", "required": True, "schema": schema})
    return parameters


def _view_class(callback: Any) -> Any:
    """Underlying class for a class-based view (plain Django `View` or DRF), if any."""
    return getattr(callback, "view_class", None) or getattr(callback, "cls", None)


def _detect_methods(callback: Any) -> list[str]:
    """
    Infer allowed HTTP methods for a view.

    Class-based views (Django's `View.as_view()` or DRF's `APIView`/`api_view`)
    expose which handlers they implement, so those are read directly. Plain
    function-based views carry no such signal, so they default to GET.
    """
    view_class = _view_class(callback)
    if view_class is not None:
        methods = [name.upper() for name in HTTP_METHOD_NAMES if hasattr(view_class, name)]
        return methods or ["GET"]
    return ["GET"]


def _summary(callback: Any) -> str:
    target = _view_class(callback) or callback
    doc = inspect.getdoc(target)
    if doc:
        return doc.strip().splitlines()[0]
    return getattr(target, "__name__", None) or type(target).__name__


def _handler_for_method(callback: Any, method: str) -> Any:
    """The concrete function that will run for this method — bound method on a CBV, or the callback itself."""
    view_class = _view_class(callback)
    if view_class is not None:
        return getattr(view_class, method.lower(), None)
    return callback


def _request_body_schema(callback: Any, method: str) -> dict[str, Any] | None:
    """
    Infer a `requestBody` schema by reading the handler's own source.

    Returns None when the handler never touches the request body (so we
    don't force a request body field onto endpoints that ignore it), a
    generic object schema when the body is read but fields can't be
    identified, or an object schema with real property names/example
    otherwise.
    """
    handler = _handler_for_method(callback, method)
    if handler is None:
        return None

    try:
        source = inspect.getsource(handler)
    except (OSError, TypeError):
        return {"type": "object"}

    if not any(marker in source for marker in BODY_MARKERS):
        return None

    fields = list(dict.fromkeys(FIELD_ACCESS_RE.findall(source)))
    if not fields:
        return {"type": "object"}

    return {
        "type": "object",
        "properties": {name: {"type": "string"} for name in fields},
        "example": {name: "" for name in fields},
    }


def _tag_for(path: str) -> str:
    first_segment = path.strip("/").split("/", 1)[0]
    return first_segment or "default"


def _normalize_path(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return SLASH_RUN_RE.sub("/", path)


def _operation_id(method: str, path: str) -> str:
    slug = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    return f"{method.lower()}_{slug or 'root'}"


def _walk(patterns: Any, prefix: str) -> Any:
    for entry in patterns:
        if isinstance(entry, URLResolver):
            yield from _walk(entry.url_patterns, prefix + _route_string(entry.pattern))
        elif isinstance(entry, URLPattern):
            yield prefix + _route_string(entry.pattern), entry


def discover_endpoints() -> list[tuple[str, URLPattern]]:
    """Walk `ROOT_URLCONF` and return every `(openapi_path, url_pattern)` pair."""
    resolver = get_resolver()
    endpoints = []
    for raw_path, url_pattern in _walk(resolver.url_patterns, ""):
        path = _normalize_path(ANGLE_PARAM_RE.sub(r"{\1}", raw_path))
        endpoints.append((path, url_pattern))
    return endpoints


def generate_openapi_schema() -> dict[str, Any]:
    """
    Build an OpenAPI 3.0 schema by introspecting the project's URLconf.

    No decorators or serializers required — paths, path parameters and
    HTTP methods are all inferred from `urlpatterns` and the views they
    point to. Override title/version/description via a `DJANGOAPI` dict
    in settings.py.
    """
    config = getattr(settings, "DJANGOAPI", {})
    paths: dict[str, Any] = {}

    for path, url_pattern in discover_endpoints():
        callback = url_pattern.callback
        methods = _detect_methods(callback)
        parameters = _path_parameters(url_pattern.pattern)
        path_item = paths.setdefault(path, {})

        for method in methods:
            operation: dict[str, Any] = {
                "summary": _summary(callback),
                "operationId": _operation_id(method, path),
                "tags": [_tag_for(path)],
                "responses": {"200": {"description": "Successful response"}},
            }
            if parameters:
                operation["parameters"] = parameters
            if method in ("POST", "PUT", "PATCH"):
                schema = _request_body_schema(callback, method)
                if schema is not None:
                    operation["requestBody"] = {
                        "content": {"application/json": {"schema": schema}}
                    }
            path_item[method.lower()] = operation

    info: dict[str, Any] = {
        "title": config.get("TITLE", "Django API"),
        "version": config.get("VERSION", "1.0.0"),
    }
    if config.get("DESCRIPTION"):
        info["description"] = config["DESCRIPTION"]

    return {
        "openapi": "3.0.3",
        "info": info,
        "paths": paths,
    }
