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

## Custom docs path

```python
DJO = {"DOCS_URL": "/api/docs", "OPENAPI_URL": "/api/openapi.json"}
```

The middleware compares the exact request path (trailing slash stripped) against these two values before falling through to normal URL resolution — so pick any path that doesn't collide with an existing route.
