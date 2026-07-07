from __future__ import annotations

from django.apps import AppConfig
from django.conf import settings

from .types import MIDDLEWARE_PATH


class DjangoAPIConfig(AppConfig):
    """
    Registers djangoapi and self-installs its middleware.

    Django only calls `ready()` once, during `django.setup()` — which
    always runs before `load_middleware()` builds the request/response
    chain (both `get_wsgi_application()` and `get_asgi_application()`
    call `django.setup()` first). Prepending here is what lets the whole
    package work from a single `INSTALLED_APPS` entry, no urls.py edits.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "djangoapi"
    verbose_name = "DjangoAPI"

    def ready(self) -> None:
        middleware = list(settings.MIDDLEWARE)
        if MIDDLEWARE_PATH not in middleware:
            settings.MIDDLEWARE = [MIDDLEWARE_PATH, *middleware]
