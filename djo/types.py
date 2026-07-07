from __future__ import annotations

import re
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


MIDDLEWARE_PATH = "djo.middleware.DjangoAPIMiddleware"