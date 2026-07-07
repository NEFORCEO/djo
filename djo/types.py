from __future__ import annotations

import datetime
import decimal
import re
import uuid
from typing import Any

ANGLE_PARAM_RE = re.compile(r"<(?:[^:<>]+:)?(\w+)>")

SLASH_RUN_RE = re.compile(r"/{2,}")

CONVERTER_SCHEMAS: dict[str, dict[str, Any]] = {
    "IntConverter": {"type": "integer"},
    "StringConverter": {"type": "string"},
    "SlugConverter": {"type": "string"},
    "UUIDConverter": {"type": "string", "format": "uuid"},
    "PathConverter": {"type": "string"},
}

HTTP_METHOD_NAMES = ("get", "post", "put", "patch", "delete")

BODY_MARKERS = ("request.body", "request.POST", "request.FILES", "request.data", "json.loads")

FIELD_ACCESS_RE = re.compile(
    r"""(?:request\.POST|request\.data|payload|data|body)\s*(?:\.get\(\s*|\[)\s*['"](\w+)['"]"""
)

QUERY_ACCESS_RE = re.compile(
    r"""request\.GET(\.get\(|\[)\s*['"](\w+)['"](?:\s*,\s*([^)\]]+))?"""
)

DRF_FIELD_SCHEMAS: dict[str, dict[str, Any]] = {
    "BooleanField": {"type": "boolean"},
    "NullBooleanField": {"type": "boolean"},
    "IntegerField": {"type": "integer"},
    "FloatField": {"type": "number"},
    "DecimalField": {"type": "number"},
    "CharField": {"type": "string"},
    "EmailField": {"type": "string", "format": "email"},
    "URLField": {"type": "string", "format": "uri"},
    "SlugField": {"type": "string"},
    "UUIDField": {"type": "string", "format": "uuid"},
    "DateField": {"type": "string", "format": "date"},
    "DateTimeField": {"type": "string", "format": "date-time"},
    "ListField": {"type": "array", "items": {"type": "string"}},
    "PrimaryKeyRelatedField": {"type": "integer"},
    "ChoiceField": {"type": "string"},
}

PUBLIC_PERMISSIONS = frozenset({"AllowAny"})

TOKEN_AUTH_MARKERS = ("Token", "JWT", "Bearer")

SECURITY_SCHEMES: dict[str, dict[str, Any]] = {
    "cookieAuth": {"type": "apiKey", "in": "cookie", "name": "sessionid"},
    "bearerAuth": {"type": "http", "scheme": "bearer"},
}

STATUS_LITERAL_RE = re.compile(r"status(?:_code)?\s*=\s*(\d{3})\b")

STATUS_CONST_RE = re.compile(r"HTTP_(\d{3})_")

EXCEPTION_STATUS_MAP: dict[str, int] = {
    "Http404": 404,
    "NotFound": 404,
    "PermissionDenied": 403,
    "ValidationError": 400,
    "NotAuthenticated": 401,
    "AuthenticationFailed": 401,
    "MethodNotAllowed": 405,
    "Throttled": 429,
    "ParseError": 400,
}

RAISE_EXCEPTION_RE = re.compile(rf"\braise\s+({'|'.join(EXCEPTION_STATUS_MAP)})\b")

MIDDLEWARE_PATH = "djo.middleware.DjangoAPIMiddleware"

ANNOTATION_SCHEMAS: dict[Any, dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number"},
    bool: {"type": "boolean"},
    list: {"type": "array", "items": {"type": "string"}},
    dict: {"type": "object"},
    uuid.UUID: {"type": "string", "format": "uuid"},
    datetime.date: {"type": "string", "format": "date"},
    datetime.datetime: {"type": "string", "format": "date-time"},
    decimal.Decimal: {"type": "number"},
}

JSON_RESPONSE_CALLS = ("JsonResponse", "Response")

INT_NAME_RE = re.compile(r"^(pk|id)$|_id$")

BOOL_NAME_PREFIXES = ("is_", "has_")
