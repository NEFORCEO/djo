# Headers & Cookies

djo reads the handler's own source for `request.headers` and `request.COOKIES` access, the same way it reads `request.GET` for [query parameters](query-parameters.md) — and turns each one into an OpenAPI parameter with `"in": "header"` / `"in": "cookie"`.

```python
def whoami(request):
    """Echo back the caller's API key and session, read from headers/cookies."""
    api_key = request.headers.get("X-API-Key")
    session = request.COOKIES.get("sessionid")
    return JsonResponse({"api_key": api_key, "session": session})
```

Expanded in Swagger UI:

![Header and cookie parameters](../../media/headers-cookies.png)

## How type and required-ness are inferred

Exactly the same rule as query parameters: `[...]` access has no fallback, so it's required; `.get(...)` always has one, so it's optional, and a literal default is used to infer a more specific type than `string`.

| Source pattern | `in` | `required` | `schema` |
|---|---|---|---|
| `request.headers["X-API-Key"]` | `header` | `true` | `{"type": "string"}` |
| `request.headers.get("X-API-Key")` | `header` | `false` | `{"type": "string"}` |
| `request.COOKIES["sessionid"]` | `cookie` | `true` | `{"type": "string"}` |
| `request.COOKIES.get("sessionid", "")` | `cookie` | `false` | `{"type": "string"}` |

## Not a substitute for auth

This is a plain, best-effort read of arbitrary header/cookie access in a handler's source — it has nothing to do with djo's [security scheme detection](security.md), which is driven by `permission_classes`/`authentication_classes`/`LoginRequiredMixin` and produces the Swagger **Authorize** button. A handler that reads a custom `X-API-Key` header for its own ad-hoc auth check still needs that logic implemented by hand; djo just documents that the header exists.
