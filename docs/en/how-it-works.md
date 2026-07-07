# How It Works

djo is four small modules. No decorators, no code generation step, no build-time work — the schema is computed fresh on every request to `/openapi.json`.

## 1. Self-installing middleware

```python
# djo/apps.py
class DjangoAPIConfig(AppConfig):
    name = "djo"

    def ready(self) -> None:
        middleware = list(settings.MIDDLEWARE)
        if MIDDLEWARE_PATH not in middleware:
            settings.MIDDLEWARE = [MIDDLEWARE_PATH, *middleware]
```

Django calls `AppConfig.ready()` exactly once, during `django.setup()` — and `django.setup()` always completes *before* `get_wsgi_application()` / `get_asgi_application()` call `load_middleware()` to build the request/response chain. That ordering is what lets `djo` prepend its own middleware to `settings.MIDDLEWARE` at import time, purely from being listed in `INSTALLED_APPS` — no `urls.py` edits, no manual `MIDDLEWARE` entry.

## 2. The middleware itself

```python
# djo/middleware.py
class DjangoAPIMiddleware:
    def __call__(self, request):
        path = request.path.rstrip("/") or "/"

        if path == self.docs_url:
            return HttpResponse(get_swagger_html(...), content_type="text/html")

        if path == self.openapi_url:
            return JsonResponse(generate_openapi_schema(), ...)

        return self.get_response(request)
```

Because it's prepended, it runs first and intercepts `/docs` and `/openapi.json` before Django's normal URL resolution ever sees them. Every other request passes straight through, untouched. One consequence: these two paths never show up as "discovered" API endpoints in the generated schema — they're handled entirely outside the URLconf walk.

## 3. Schema generation

```python
# djo/generator.py
def generate_openapi_schema() -> dict:
    for path, url_pattern in discover_endpoints():
        ...
```

`discover_endpoints()` recursively walks `get_resolver().url_patterns`, distinguishing `URLResolver` (nested `include()`s) from `URLPattern` (leaf views), and converts Django's `<int:pk>`-style route syntax into OpenAPI's `{pk}` syntax. For each leaf, djo reads:

- **Path parameters** from `RoutePattern.converters` (empty for `re_path()`).
- **HTTP methods** from which of `get`/`post`/`put`/`patch`/`delete` the view class implements (function views default to `GET`).
- **Query parameters**, **request/response bodies**, **security requirements**, and **error responses** — each covered in its own page under [Features](features/index.md).

Nothing here executes your view code. Bodies and errors are inferred by reading the concrete handler's source with `inspect.getsource()` and matching a handful of regexes against it; serializers and permission classes are read as static class attributes.

## 4. Swagger UI

```python
# djo/swagger.py
SWAGGER_HTML = """<!DOCTYPE html>
...
<style> html, body { margin: 0; background: #ffffff; } .topbar { display: none; } </style>
...
"""
```

A single HTML template pointing `swagger-ui-dist` (loaded from a CDN) at `/openapi.json`, styled white/plain rather than the library's default dark theme. A small `requestInterceptor` reads the `csrftoken` cookie and attaches it as `X-CSRFToken` on unsafe methods, so **Try it out** works against real, CSRF-protected Django views without any extra setup.

## Design principles

- **Introspection over annotation.** If Django or DRF already knows something about a view (converters, serializer fields, permission classes), djo reads it — it never asks you to repeat that information in a decorator.
- **Best-effort, not a type checker.** Source-based inference (query params, request bodies, error codes) is a heuristic, not a guarantee — see the notes on each [feature page](features/index.md) for exactly what it can and can't see.
- **Nothing executes.** Views, serializers' `__init__`/`get_fields()` calls aside, no view code or handler logic ever runs during schema generation.
