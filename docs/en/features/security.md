# Security Schemes

djo detects auth requirements straight off view classes — nothing is instantiated, nothing is called — and adds a matching entry to `components.securitySchemes`, a lock icon on the operation, and an **Authorize** button in Swagger UI.

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class ProtectedUserList(LoginRequiredMixin, View):
    """List users — requires an authenticated session."""

    def get(self, request):
        ...
```

![Security scheme](../../media/security.png)

The **Authorize** button lets you paste a session cookie or bearer token once and have it applied to every subsequent "Try it out" call — see the top-right corner in the [Quick Start](../quick-start.md) screenshot.

## What's checked

| Signal | Where it comes from | Scheme |
|---|---|---|
| `LoginRequiredMixin` in the view's MRO | Plain Django | `cookieAuth` |
| `permission_classes` containing anything other than `AllowAny` | DRF | `cookieAuth` (default) |
| `authentication_classes` containing a class with `Token`, `JWT`, or `Bearer` in its name | DRF | `bearerAuth` |

A view with `permission_classes = [AllowAny]` (or no `permission_classes` / `LoginRequiredMixin` at all) is treated as public — no `security` requirement, no lock icon.

## Emitted schemes

```json
{
  "cookieAuth": { "type": "apiKey", "in": "cookie", "name": "sessionid" },
  "bearerAuth": { "type": "http", "scheme": "bearer" }
}
```

Only schemes actually referenced by at least one operation are added to `components.securitySchemes` — a project with no protected views gets no `Authorize` button at all.

## DRF token/JWT auth

```python
class ProductListCreateView(ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]  # or JWTAuthentication, etc.
```

Because `TokenAuthentication` matches the `Token` marker, this view is documented with `bearerAuth` instead of the default `cookieAuth` — Swagger UI's Authorize dialog will prompt for a bearer token accordingly.
