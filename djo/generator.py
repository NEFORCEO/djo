from __future__ import annotations

import ast
import inspect
import textwrap
from http import HTTPStatus
from typing import Any, Literal, Union, get_args, get_origin

from django.conf import settings
from django.urls import get_resolver
from django.urls.resolvers import RoutePattern, URLPattern, URLResolver

from .types import (
    ANGLE_PARAM_RE,
    ANNOTATION_SCHEMAS,
    BODY_MARKERS,
    BOOL_NAME_PREFIXES,
    CONVERTER_SCHEMAS,
    DRF_FIELD_SCHEMAS,
    EXCEPTION_STATUS_MAP,
    FIELD_ACCESS_RE,
    HTTP_METHOD_NAMES,
    INT_NAME_RE,
    JSON_RESPONSE_CALLS,
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


def _annotation_schema(annotation: Any) -> dict[str, Any] | None:
    """OpenAPI schema for a plain type annotation; unwraps `Optional[X]`/`X | None`."""
    if annotation is inspect.Signature.empty:
        return None

    origin = get_origin(annotation)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) != 1:
            return None
        annotation = args[0]
        origin = get_origin(annotation)

    if origin in (list, tuple, set):
        args = get_args(annotation)
        items = ANNOTATION_SCHEMAS.get(args[0], {"type": "string"}) if args else {"type": "string"}
        return {"type": "array", "items": items}

    return ANNOTATION_SCHEMAS.get(annotation)


def _annotated_parameters(
    callback: Any, method: str, path_param_names: set[str]
) -> dict[str, dict[str, Any]]:
    """
    Extra handler parameters beyond `request`/`self`/path params, keyed by name.

    Django never passes these automatically, but a typed signature (e.g.
    `def create(request, name: str, age: int)`) is a precise, explicit signal
    of the fields a view expects — it beats guessing types from regex-matched
    source, so it's preferred wherever it's available.
    """
    handler = _handler_for_method(callback, method)
    if handler is None:
        return {}
    try:
        signature = inspect.signature(handler)
    except (TypeError, ValueError):
        return {}

    fields = {}
    for name, param in signature.parameters.items():
        if name in ("self", "request") or name in path_param_names:
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        schema = _annotation_schema(param.annotation)
        if schema is None:
            continue
        fields[name] = {"schema": schema, "required": param.default is param.empty}
    return fields


def _request_body_schema(
    callback: Any, method: str, serializer_class: Any, path_param_names: set[str]
) -> dict[str, Any] | None:
    """
    Infer a `requestBody` schema, preferring a declared DRF serializer, then a
    typed handler signature, and falling back to reading the handler's source.

    Returns None when nothing finds evidence the body is used, so we don't
    force a request body field onto endpoints that ignore it.
    """
    if serializer_class is not None:
        schema = _schema_from_serializer(serializer_class, direction="request")
        if schema is not None:
            return schema

    annotated = _annotated_parameters(callback, method, path_param_names)
    if annotated:
        properties = {name: field["schema"] for name, field in annotated.items()}
        required = [name for name, field in annotated.items() if field["required"]]
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
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


def _query_parameters(callback: Any, method: str, path_param_names: set[str]) -> list[dict[str, Any]]:
    """
    OpenAPI query parameters, preferring typed signature parameters and
    falling back to `request.GET` access patterns in the handler's source.

    Signature-typed extras are only read as query params for methods with no
    request body (`_request_body_schema` claims them for POST/PUT/PATCH
    instead), so a typed parameter never shows up in both places at once.
    """
    annotated = {} if method in ("POST", "PUT", "PATCH") else _annotated_parameters(
        callback, method, path_param_names
    )
    parameters = [
        {"name": name, "in": "query", "required": field["required"], "schema": field["schema"]}
        for name, field in annotated.items()
    ]

    source = _handler_source(callback, method)
    if not source:
        return parameters

    seen = set(annotated)
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


def _identifier_hint_schema(identifier: str) -> dict[str, Any] | None:
    """A schema guessed from a bare identifier's name (`pk`, `user_id`, `is_active`, ...)."""
    if INT_NAME_RE.search(identifier):
        return {"type": "integer"}
    if identifier.startswith(BOOL_NAME_PREFIXES):
        return {"type": "boolean"}
    return None


def _ast_value_schema(node: ast.expr, param_schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Best-effort OpenAPI schema for one value expression inside a response dict literal.

    `param_schemas` carries the types already known from typed handler
    parameters (see `_annotated_parameters`) — a bare `name` in the response
    that echoes a typed parameter of the same name is a much stronger signal
    than the identifier-name heuristic, so it's checked first.
    """
    if isinstance(node, ast.Name) and node.id in param_schemas:
        return param_schemas[node.id]
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return {"type": "boolean"}
        if isinstance(node.value, int):
            return {"type": "integer"}
        if isinstance(node.value, float):
            return {"type": "number"}
        return {"type": "string"}
    if isinstance(node, (ast.List, ast.Tuple)):
        items = _ast_value_schema(node.elts[0], param_schemas) if node.elts else {"type": "string"}
        return {"type": "array", "items": items}
    if isinstance(node, ast.Dict):
        return _ast_dict_schema(node, param_schemas) or {"type": "object"}
    if isinstance(node, ast.Name):
        return _identifier_hint_schema(node.id) or {"type": "string"}
    if isinstance(node, ast.Attribute):
        return _identifier_hint_schema(node.attr) or {"type": "string"}
    return {"type": "string"}


def _ast_dict_schema(node: ast.Dict, param_schemas: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Object schema for an `ast.Dict` literal, skipping any non-string/`**spread` keys."""
    properties = {}
    for key, value in zip(node.keys, node.values, strict=True):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            properties[key.value] = _ast_value_schema(value, param_schemas)
    return {"type": "object", "properties": properties} if properties else None


class _ReturnedResponseVisitor(ast.NodeVisitor):
    """Finds the first `return JsonResponse({...})` / `return Response({...})` in a handler."""

    def __init__(self, param_schemas: dict[str, dict[str, Any]]) -> None:
        self.param_schemas = param_schemas
        self.schema: dict[str, Any] | None = None

    def visit_Return(self, node: ast.Return) -> None:
        if self.schema is not None or not isinstance(node.value, ast.Call):
            return
        call = node.value
        if not (isinstance(call.func, ast.Name) and call.func.id in JSON_RESPONSE_CALLS):
            return
        if not call.args:
            return

        payload = call.args[0]
        if isinstance(payload, ast.Dict):
            self.schema = _ast_dict_schema(payload, self.param_schemas)
        elif isinstance(payload, (ast.List, ast.Tuple)) and payload.elts:
            first = payload.elts[0]
            item_schema = _ast_dict_schema(first, self.param_schemas) if isinstance(first, ast.Dict) else None
            if item_schema is not None:
                self.schema = {"type": "array", "items": item_schema}


def _response_schema_from_source(
    source: str, param_schemas: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Best-effort response schema read from a handler's `return JsonResponse({...})` literal."""
    if not source:
        return None
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None
    visitor = _ReturnedResponseVisitor(param_schemas)
    visitor.visit(tree)
    return visitor.schema


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
    callback: Any, method: str, serializer_class: Any, mro_names: set[str], path_param_names: set[str]
) -> dict[str, Any]:
    """
    Assemble the `responses` object for one operation: success code + body,
    plus inferred errors.

    The response body prefers a declared DRF serializer, then falls back to
    reading a literal `JsonResponse({...})`/`Response({...})` off the
    handler's own source — cross-referenced against any typed handler
    parameters so a returned `name` echoing a `name: str` argument picks up
    its real type instead of a generic string guess.
    """
    success_code = "201" if method == "POST" and "CreateModelMixin" in mro_names else "200"
    success_description = "Created" if success_code == "201" else "Successful response"
    responses: dict[str, Any] = {success_code: {"description": success_description}}

    schema = None
    if serializer_class is not None:
        schema = _schema_from_serializer(serializer_class, direction="response")
        if schema is not None and method == "GET" and "ListModelMixin" in mro_names:
            schema = {"type": "array", "items": schema}
    if schema is None:
        annotated = _annotated_parameters(callback, method, path_param_names)
        param_schemas = {name: field["schema"] for name, field in annotated.items()}
        schema = _response_schema_from_source(_handler_source(callback, method), param_schemas)
    if schema is not None:
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
        path_param_names = {parameter["name"] for parameter in path_parameters}
        serializer_class = _serializer_class(view_class)
        mro_names = _mro_names(view_class)
        security = _security_requirement(view_class, mro_names)
        used_security_schemes.update(security)
        path_item = paths.setdefault(path, {})

        for method in methods:
            parameters = path_parameters + _query_parameters(callback, method, path_param_names)

            operation: dict[str, Any] = {
                "summary": _summary(callback),
                "operationId": _operation_id(method, path),
                "tags": [_tag_for(path)],
                "responses": _build_responses(
                    callback, method, serializer_class, mro_names, path_param_names
                ),
            }
            if parameters:
                operation["parameters"] = parameters
            if method in ("POST", "PUT", "PATCH"):
                body_schema = _request_body_schema(callback, method, serializer_class, path_param_names)
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
