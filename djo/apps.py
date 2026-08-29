from __future__ import annotations

from django.apps import AppConfig
from django.conf import settings

from .types import MIDDLEWARE_PATH, SECURITY_MIDDLEWARE_PATH


class DjangoAPIConfig(AppConfig):
    """
    Registers djo and self-installs its middleware.

    Django only calls `ready()` once, during `django.setup()` — which
    always runs before `load_middleware()` builds the request/response
    chain (both `get_wsgi_application()` and `get_asgi_application()`
    call `django.setup()` first). Inserting here is what lets the whole
    package work from a single `INSTALLED_APPS` entry, no urls.py edits.

    The middleware goes directly *after* `SecurityMiddleware` (or at the
    front if that isn't installed), so `/docs` still gets `SECURE_SSL_REDIRECT`,
    HSTS and the other security headers applied to it.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "djo"
    verbose_name = "Djo"

    def ready(self) -> None:
        middleware = list(settings.MIDDLEWARE)
        if MIDDLEWARE_PATH in middleware:
            return
        try:
            index = middleware.index(SECURITY_MIDDLEWARE_PATH) + 1
        except ValueError:
            index = 0
        middleware.insert(index, MIDDLEWARE_PATH)
        settings.MIDDLEWARE = middleware
