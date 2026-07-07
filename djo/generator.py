from __future__ import annotations

import inspect
from http import HTTPStatus
from typing import Any, Literal

from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import RoutePattern, URLPattern, URLResolver

from .types import (
    ANGLE_PARAM_RE,
    BODY_MARKERS,
    CONVERTER_SCHEMAS,
    DRF_FIELD_SCHEMAS,
    EXCEPTION_STATUS_MAP,
    FIELD_ACCESS_RE,
    HTTP_METHOD_NAMES,
    PUBLIC_PERMISSIONS,
    QUERY_ACCESS_RE,
    RAISE_EXCEPTION_RE,
    SECURITY_SCHEMES,
    SLASH_RUN_RE,
    STATUS_CONST_RE,
    STATUS_LITERAL_RE,
    TOKEN_AUTH_MARKERS,
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


def _infer_literal_schema(literal: str | None) -> dict[str, Any]:
    """Best-effort OpenAPI schema for a default-value literal like `1` or `"active"`."""
    if literal is None:
        return {"type": "string"}
    literal = literal.strip().strip("'\"")
    if literal in ("True", "False"):
        return {"type": "boolean"}
    if literal.lstrip("-").isdigit():
        return {"type": "integer"}
    try:
        float(literal)
        return {"type": "number"}
    except ValueError:
        return {"type": "string"}


def _view_class(callback: Any) -> Any:
    """Underlying class for a class-based view (plain Django `View` or DRF), if any."""
    return getattr(callback, "view_class", None) or getattr(callback, "cls", None)


def _mro_names(view_class: Any) -> set[str]:
    return {cls.__name__ for cls in view_class.__mro__} if view_class is not None else set()


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


def _handler_source(callback: Any, method: str) -> str:
    """Best-effort source of the concrete handler; empty string when it can't be read."""
    handler = _handler_for_method(callback, method)
    if handler is None:
        return ""
    try:
        return inspect.getsource(handler)
    except (OSError, TypeError):
        return ""


def _serializer_class(view_class: Any) -> Any:
    """
    The DRF `serializer_class` declared directly on a view, if any.

    Only the static attribute is read — `get_serializer_class()` is never
    called, since projects often override it with logic that expects a
    live request/instance to run safely.
    """
    return getattr(view_class, "serializer_class", None)


def _schema_from_serializer(
    serializer_class: Any, *, direction: Literal["request", "response"]
) -> dict[str, Any] | None:
    """
    Build an object schema straight from a DRF serializer's declared fields.

    `direction="request"` drops read-only fields and marks required ones;
    `direction="response"` drops write-only fields (e.g. passwords).
    """
    try:
        fields = serializer_class().get_fields()
    except Exception:
        return None

    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, field in fields.items():
        if direction == "request" and getattr(field, "read_only", False):
            continue
        if direction == "response" and getattr(field, "write_only", False):
            continue

        schema = dict(DRF_FIELD_SCHEMAS.get(type(field).__name__, {"type": "string"}))
        choices = getattr(field, "choices", None)
        if choices:
            schema["enum"] = list(choices)
        properties[name] = schema

        if direction == "request" and getattr(field, "required", False):
            required.append(name)

    if not properties:
        return None

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _request_body_schema(callback: Any, method: str, serializer_class: Any) -> dict[str, Any] | None:
    """
    Infer a `requestBody` schema, preferring a declared DRF serializer and
    falling back to reading the handler's own source.

    Returns None when neither source finds evidence the body is used, so we
    don't force a request body field onto endpoints that ignore it.
    """
    if serializer_class is not None:
        schema = _schema_from_serializer(serializer_class, direction="request")
        if schema is not None:
            return schema

    source = _handler_source(callback, method)
    if not source or not any(marker in source for marker in BODY_MARKERS):
        return None

    fields = list(dict.fromkeys(FIELD_ACCESS_RE.findall(source)))
    if not fields:
        return {"type": "object"}

    return {
        "type": "object",
        "properties": {name: {"type": "string"} for name in fields},
        "example": {name: "" for name in fields},
    }


def _query_parameters(callback: Any, method: str) -> list[dict[str, Any]]:
    """OpenAPI query parameters inferred from `request.GET` access in the handler's source."""
    source = _handler_source(callback, method)
    if not source:
        return []

    parameters = []
    seen: set[str] = set()
    for access, name, default in QUERY_ACCESS_RE.findall(source):
        if name in seen:
            continue
        seen.add(name)
        required = access == "["
        parameters.append(
            {
                "name": name,
                "in": "query",
                "required": required,
                "schema": _infer_literal_schema(None if required else default or None),
            }
        )
    return parameters


def _error_responses(callback: Any, method: str) -> dict[str, Any]:
    """Extra response codes inferred from status literals/constants and raised exceptions."""
    source = _handler_source(callback, method)
    if not source:
        return {}

    codes = {int(code) for code in STATUS_LITERAL_RE.findall(source)}
    codes |= {int(code) for code in STATUS_CONST_RE.findall(source)}
    codes |= {EXCEPTION_STATUS_MAP[name] for name in RAISE_EXCEPTION_RE.findall(source)}

    responses = {}
    for code in sorted(codes):
        try:
            responses[str(code)] = {"description": HTTPStatus(code).phrase}
        except ValueError:
            continue
    return responses


def _security_requirement(view_class: Any, mro_names: set[str]) -> tuple[str, ...]:
    """
    Best-effort auth requirement for a view, read straight off the class —
    nothing is instantiated or called. Recognizes DRF's `permission_classes`
    / `authentication_classes` and Django's `LoginRequiredMixin`.
    """
    if view_class is None:
        return ()

    permission_names = {cls.__name__ for cls in getattr(view_class, "permission_classes", ())}
    auth_names = {cls.__name__ for cls in getattr(view_class, "authentication_classes", ())}

    requires_auth = "LoginRequiredMixin" in mro_names or bool(permission_names - PUBLIC_PERMISSIONS)
    if not requires_auth:
        return ()

    if any(marker in name for name in auth_names for marker in TOKEN_AUTH_MARKERS):
        return ("bearerAuth",)
    return ("cookieAuth",)


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


def _build_responses(
    callback: Any, method: str, serializer_class: Any, mro_names: set[str]
) -> dict[str, Any]:
    """Assemble the `responses` object for one operation: success code + body, plus inferred errors."""
    success_code = "201" if method == "POST" and "CreateModelMixin" in mro_names else "200"
    success_description = "Created" if success_code == "201" else "Successful response"
    responses: dict[str, Any] = {success_code: {"description": success_description}}

    if serializer_class is not None:
        schema = _schema_from_serializer(serializer_class, direction="response")
        if schema is not None:
            if method == "GET" and "ListModelMixin" in mro_names:
                schema = {"type": "array", "items": schema}
            responses[success_code]["content"] = {"application/json": {"schema": schema}}

    error_responses = _error_responses(callback, method)
    error_responses.pop(success_code, None)
    responses.update(error_responses)
    return responses


def generate_openapi_schema() -> dict[str, Any]:
    """
    Build an OpenAPI 3.0 schema by introspecting the project's URLconf.

    No decorators or serializers required — paths, path parameters and HTTP
    methods are all inferred from `urlpatterns` and the views they point to.
    When a view declares a DRF `serializer_class`, it's used for accurate
    request/response schemas; otherwise both are inferred from the handler's
    own source. Override title/version/description via a `DJO` dict in
    settings.py.
    """
    config = getattr(settings, "DJO", {})
    paths: dict[str, Any] = {}
    used_security_schemes: set[str] = set()

    for path, url_pattern in discover_endpoints():
        callback = url_pattern.callback
        view_class = _view_class(callback)
        methods = _detect_methods(callback)
        path_parameters = _path_parameters(url_pattern.pattern)
        serializer_class = _serializer_class(view_class)
        mro_names = _mro_names(view_class)
        security = _security_requirement(view_class, mro_names)
        used_security_schemes.update(security)
        path_item = paths.setdefault(path, {})

        for method in methods:
            parameters = path_parameters + _query_parameters(callback, method)

            operation: dict[str, Any] = {
                "summary": _summary(callback),
                "operationId": _operation_id(method, path),
                "tags": [_tag_for(path)],
                "responses": _build_responses(callback, method, serializer_class, mro_names),
            }
            if parameters:
                operation["parameters"] = parameters
            if method in ("POST", "PUT", "PATCH"):
                body_schema = _request_body_schema(callback, method, serializer_class)
                if body_schema is not None:
                    operation["requestBody"] = {"content": {"application/json": {"schema": body_schema}}}
            if security:
                operation["security"] = [{scheme: []} for scheme in security]

            path_item[method.lower()] = operation

    info: dict[str, Any] = {
        "title": config.get("TITLE", "Django API"),
        "version": config.get("VERSION", "1.0.0"),
    }
    if config.get("DESCRIPTION"):
        info["description"] = config["DESCRIPTION"]

    schema: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": info,
        "paths": paths,
    }
    if used_security_schemes:
        schema["components"] = {
            "securitySchemes": {name: SECURITY_SCHEMES[name] for name in sorted(used_security_schemes)}
        }
    return schema
