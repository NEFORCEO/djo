from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.utils.module_loading import import_string


def config() -> dict[str, Any]:
    """The `DJO` settings dict, or an empty dict when unset."""
    return getattr(settings, "DJO", None) or {}


def is_enabled() -> bool:
    """
    Whether djo should serve `/docs` and `/openapi.json` at all.

    Defaults to `settings.DEBUG`, so a plain `pip install djo` + an
    `INSTALLED_APPS` entry never publishes the API surface (paths, inferred
    bodies, auth requirements, error codes) on a production deployment by
    accident. Set `DJO = {"ENABLED": True}` to force it on — typically
    together with a `GATE` callback that restricts who can reach it.
    """
    enabled = config().get("ENABLED")
    if enabled is None:
        return bool(getattr(settings, "DEBUG", False))
    return bool(enabled)


def get_gate() -> Callable[[HttpRequest], bool] | None:
    """
    Optional per-request predicate guarding the docs endpoints.

    `DJO = {"GATE": "myapp.docs.is_staff"}` (a dotted path) or a direct
    callable. It receives the `HttpRequest` and returns truthy to allow the
    request through; a falsy return makes djo fall through as if it weren't
    installed (normal URL resolution / 404).
    """
    gate = config().get("GATE")
    if gate is None:
        return None
    if isinstance(gate, str):
        gate = import_string(gate)
    if not callable(gate):
        raise TypeError("DJO['GATE'] must be a callable or a dotted import path")
    return gate
