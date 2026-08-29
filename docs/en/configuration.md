# Configuration

Everything is optional — djo works with sane defaults out of the box. Override title, version, description, or the docs paths themselves via a `DJO` dict in `settings.py`:

```python
DJO = {
    "TITLE": "My API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Internal API for the mobile app.",
    "DOCS_URL": "/docs",
    "OPENAPI_URL": "/openapi.json",
}
```

| Key | Default | Description |
|---|---|---|
| `TITLE` | `"Django API"` | Shown in the Swagger UI header and in `info.title`. |
| `VERSION` | `"1.0.0"` | Version string next to the title, and `info.version`. |
| `DESCRIPTION` | *(none)* | Markdown description in `info.description`. Omitted entirely when unset. |
| `DOCS_URL` | `"/docs"` | Path the Swagger UI page is served on. |
| `OPENAPI_URL` | `"/openapi.json"` | Path the raw OpenAPI 3.0 JSON schema is served on. |
| `ENABLED` | `settings.DEBUG` | Master switch for both endpoints. When falsy, djo falls through as if it weren't installed. |
| `GATE` | *(none)* | Callable or dotted import path, `f(request) -> bool`. Runs on every docs request; a falsy return hides the docs. |
| `SWAGGER_CSS_URL` | jsDelivr CDN | Stylesheet URL for the Swagger UI page. |
| `SWAGGER_JS_URL` | jsDelivr CDN | `swagger-ui-bundle.js` URL. |
| `SWAGGER_PRESET_JS_URL` | jsDelivr CDN | `swagger-ui-standalone-preset.js` URL. |
| `SWAGGER_CSS_SRI` / `SWAGGER_JS_SRI` / `SWAGGER_PRESET_JS_SRI` | pinned `sha512` | Subresource Integrity hash for each asset. Auto-dropped when the matching URL is overridden. |

## Custom docs path

```python
DJO = {"DOCS_URL": "/api/docs", "OPENAPI_URL": "/api/openapi.json"}
```

The middleware compares the request path (leading/trailing slashes normalized) against these two values before falling through to normal URL resolution — so pick any path that doesn't collide with an existing route. Only `GET` and `HEAD` are served; other methods get `405 Method Not Allowed`.

## Enabling in production

Both endpoints expose your entire API surface — paths, inferred request bodies, auth requirements, error codes. `ENABLED` defaults to `settings.DEBUG` so a plain `pip install` never publishes that on a production deploy by accident. Turn it on explicitly, ideally behind your own auth:

```python
DJO = {
    "ENABLED": True,
    "GATE": "myapp.docs.is_staff",
}
```

```python
# myapp/docs.py
def is_staff(request):
    return request.user.is_authenticated and request.user.is_staff
```

`GATE` runs on every request to `DOCS_URL` / `OPENAPI_URL`; when it returns falsy, djo hands the request back to normal URL resolution (typically a 404).

## Middleware placement

`DjangoAPIConfig.ready()` inserts the middleware directly after `django.middleware.security.SecurityMiddleware` (or at the front of the list if it isn't present), so `SECURE_SSL_REDIRECT`, HSTS and the other security headers still apply to `/docs`.

## Self-hosting Swagger UI

The Swagger UI CSS/JS default to a version-pinned jsDelivr build guarded by Subresource Integrity hashes. For offline or strict-CSP deployments, serve your own copies of `swagger-ui-dist`:

```python
DJO = {
    "SWAGGER_CSS_URL": "/static/swagger-ui/swagger-ui.css",
    "SWAGGER_JS_URL": "/static/swagger-ui/swagger-ui-bundle.js",
    "SWAGGER_PRESET_JS_URL": "/static/swagger-ui/swagger-ui-standalone-preset.js",
}
```

Overriding a URL drops the bundled SRI hash for that asset (it wouldn't match a different file). Pass `SWAGGER_CSS_SRI` / `SWAGGER_JS_SRI` / `SWAGGER_PRESET_JS_SRI` alongside to keep integrity checking on your own assets.
