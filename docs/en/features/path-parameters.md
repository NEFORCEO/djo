# Path Parameters

djo reads path parameters straight from Django's own `path()` converters — no annotation needed.

```python
# urls.py
urlpatterns = [
    path("users/<int:pk>/", views.UserDetail.as_view()),
]
```

produces:

```json
{
  "name": "pk",
  "in": "path",
  "required": true,
  "schema": { "type": "integer" }
}
```

## Supported converters

| Django converter | OpenAPI schema |
|---|---|
| `int` | `{"type": "integer"}` |
| `str` | `{"type": "string"}` |
| `slug` | `{"type": "string"}` |
| `uuid` | `{"type": "string", "format": "uuid"}` |
| `path` | `{"type": "string"}` |
| custom / unknown | `{"type": "string"}` (fallback) |

## `re_path()` routes

Routes declared with `re_path()` carry no converter information, so djo can't infer typed parameters from them — they're included in the schema with no `parameters` entry. Prefer `path()` with converters when you want typed docs.

## HTTP method detection

Methods are read off the view, not guessed from the URL:

- **Class-based views** (Django's `View` or DRF's `APIView`/`api_view`) — djo checks which of `get`, `post`, `put`, `patch`, `delete` the class actually implements.
- **Function-based views** — always documented as `GET`, since Django gives no other signal (see the note in the [Features overview](index.md)).

```python
class UserDetail(View):
    """Retrieve, update or delete a single user by id."""

    def get(self, request, pk): ...
    def put(self, request, pk): ...
    def delete(self, request, pk): ...
```

This produces three operations on `/users/{pk}/` — `GET`, `PUT`, `DELETE` — and nothing for `POST`/`PATCH`, since `UserDetail` doesn't implement them.
