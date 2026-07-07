# Error Responses

Alongside the success response, djo scans the handler's source for status codes and raised exceptions, and adds a matching entry per code it finds.

```python
from django.http import Http404, JsonResponse


def get_user_or_404(request, pk):
    """Look up a single user, or 404 if it doesn't exist."""
    if pk != 1:
        raise Http404("User not found")
    return JsonResponse({"id": pk, "name": "Ada"})
```

![Error responses](../../media/error-responses.png)

## What's detected

| Pattern | Example | Status code(s) |
|---|---|---|
| `status=` / `status_code=` literal | `JsonResponse(..., status=404)` | the literal value |
| DRF `status.HTTP_xxx_*` constants | `Response(..., status=status.HTTP_400_BAD_REQUEST)` | parsed from the constant name |
| Raised exceptions | `raise Http404`, `raise NotFound`, `raise ValidationError`, `raise PermissionDenied`, `raise NotAuthenticated`, `raise AuthenticationFailed`, `raise MethodNotAllowed`, `raise Throttled`, `raise ParseError` | mapped to their standard HTTP code |

Descriptions come from Python's own `http.HTTPStatus` — `404` becomes `"Not Found"`, `403` becomes `"Forbidden"`, and so on, with no hardcoded strings to keep in sync.

## Success codes aren't left out

The success response is computed first — `200` by default, or `201 Created` for a `POST` on a DRF `CreateModelMixin` view — and any error code that happens to collide with it (say, an explicit `status=200` literal) is discarded rather than overwriting the richer success entry (which may carry a response schema; see [DRF Serializers](drf-serializers.md)).

## This only reads source, nothing runs

Just like [request body](request-bodies.md) and [query parameter](query-parameters.md) inference, this is regex-based source scanning — no code path in the handler is actually executed, so a `raise Http404` deep inside a conditional you never hit in practice will still show up in the docs. Treat it as "codes this handler is capable of returning," not "codes it definitely will."
