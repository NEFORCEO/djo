from __future__ import annotations

SWAGGER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Docs</title>
    <link rel="icon" type="image/png" href="https://static.djangoproject.com/img/icon-touch.e4872c4da341.png">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css">
    <style>
        html, body { margin: 0; background: #ffffff; }
        .topbar { display: none; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" charset="UTF-8"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
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


def get_swagger_html(*, openapi_url: str = "/openapi.json") -> str:
    return SWAGGER_HTML.replace("__OPENAPI_URL__", openapi_url)
