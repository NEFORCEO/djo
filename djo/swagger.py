from __future__ import annotations

from .config import config
from .types import (
    SWAGGER_BUNDLE_JS_SRI,
    SWAGGER_BUNDLE_JS_URL,
    SWAGGER_CSS_SRI,
    SWAGGER_CSS_URL,
    SWAGGER_PRESET_JS_SRI,
    SWAGGER_PRESET_JS_URL,
)

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Docs</title>
    <link rel="icon" type="image/png" href="https://static.djangoproject.com/img/icon-touch.e4872c4da341.png">
    <link rel="stylesheet" href="__CSS_URL__"__CSS_SRI__>
    <style>
        html, body { margin: 0; background: #ffffff; }
        .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="__BUNDLE_JS_URL__"__BUNDLE_JS_SRI__></script>
    <script src="__PRESET_JS_URL__"__PRESET_JS_SRI__></script>
    <script>
        function getCookie(name) {
            const match = document.cookie.match("(^|;\\\\s*)" + name + "=([^;]*)");
            return match ? decodeURIComponent(match[2]) : null;
        }

        window.ui = SwaggerUIBundle({
            url: "__OPENAPI_URL__",
            dom_id: "#swagger-ui",
            deepLinking: true,
            filter: true,
            persistAuthorization: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout",
            requestInterceptor: function(req) {
                // Django rejects unsafe methods without a CSRF token when
                // session auth is active — forward the cookie automatically
                // so "Try it out" works against real endpoints out of the box.
                const method = (req.method || "GET").toUpperCase();
                if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
                    const token = getCookie("csrftoken");
                    if (token) {
                        req.headers["X-CSRFToken"] = token;
                    }
                }
                return req;
            }
        });
    </script>
</body>
</html>
"""


def _sri_attr(value: str) -> str:
    """Render an `integrity`/`crossorigin` attribute pair, or nothing when empty."""
    if not value:
        return ""
    return f' integrity="{value}" crossorigin="anonymous"'


def get_swagger_html(*, openapi_url: str = "/openapi.json") -> str:
    """
    Render the Swagger UI page.

    The CSS/JS assets default to a version-pinned CDN build guarded by
    Subresource Integrity hashes. Point them at your own copies (e.g. a
    self-hosted `swagger-ui-dist` for offline or strict-CSP deployments) via
    the `DJO` dict:

        DJO = {
            "SWAGGER_CSS_URL": "/static/swagger-ui/swagger-ui.css",
            "SWAGGER_JS_URL": "/static/swagger-ui/swagger-ui-bundle.js",
            "SWAGGER_PRESET_JS_URL": "/static/swagger-ui/swagger-ui-standalone-preset.js",
        }

    Overriding a URL drops its bundled SRI hash (it wouldn't match a
    different file); supply `SWAGGER_CSS_SRI` / `SWAGGER_JS_SRI` /
    `SWAGGER_PRESET_JS_SRI` to keep integrity checking on your own assets.
    """
    cfg = config()

    css_url = cfg.get("SWAGGER_CSS_URL", SWAGGER_CSS_URL)
    bundle_url = cfg.get("SWAGGER_JS_URL", SWAGGER_BUNDLE_JS_URL)
    preset_url = cfg.get("SWAGGER_PRESET_JS_URL", SWAGGER_PRESET_JS_URL)

    css_sri = cfg.get("SWAGGER_CSS_SRI", SWAGGER_CSS_SRI if css_url == SWAGGER_CSS_URL else "")
    bundle_sri = cfg.get(
        "SWAGGER_JS_SRI", SWAGGER_BUNDLE_JS_SRI if bundle_url == SWAGGER_BUNDLE_JS_URL else ""
    )
    preset_sri = cfg.get(
        "SWAGGER_PRESET_JS_SRI", SWAGGER_PRESET_JS_SRI if preset_url == SWAGGER_PRESET_JS_URL else ""
    )

    return (
        SWAGGER_HTML.replace("__CSS_URL__", css_url)
        .replace("__CSS_SRI__", _sri_attr(css_sri))
        .replace("__BUNDLE_JS_URL__", bundle_url)
        .replace("__BUNDLE_JS_SRI__", _sri_attr(bundle_sri))
        .replace("__PRESET_JS_URL__", preset_url)
        .replace("__PRESET_JS_SRI__", _sri_attr(preset_sri))
        .replace("__OPENAPI_URL__", openapi_url)
    )
