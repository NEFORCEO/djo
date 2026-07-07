# Path-параметры

djo читает path-параметры напрямую из конвертеров `path()` Django — никаких аннотаций не нужно.

```python
# urls.py
urlpatterns = [
    path("users/<int:pk>/", views.UserDetail.as_view()),
]
```

даёт:

```json
{
  "name": "pk",
  "in": "path",
  "required": true,
  "schema": { "type": "integer" }
}
```

## Поддерживаемые конвертеры

| Конвертер Django | Схема OpenAPI |
|---|---|
| `int` | `{"type": "integer"}` |
| `str` | `{"type": "string"}` |
| `slug` | `{"type": "string"}` |
| `uuid` | `{"type": "string", "format": "uuid"}` |
| `path` | `{"type": "string"}` |
| кастомный / неизвестный | `{"type": "string"}` (по умолчанию) |

## Маршруты через `re_path()`

Маршруты, объявленные через `re_path()`, не несут информации о конвертерах, поэтому djo не может определить типизированные параметры из них — они попадают в схему без секции `parameters`. Используйте `path()` с конвертерами, если хотите типизированную документацию.

## Определение HTTP-методов

Методы читаются с самого view, а не угадываются по URL:

- **Class-based view** (Django `View` или DRF `APIView`/`api_view`) — djo проверяет, какие из `get`, `post`, `put`, `patch`, `delete` класс реально реализует.
- **Function-based view** — всегда документируется как `GET`, поскольку Django не даёт другого сигнала (см. примечание в [обзоре возможностей](index.md)).

```python
class UserDetail(View):
    """Retrieve, update or delete a single user by id."""

    def get(self, request, pk): ...
    def put(self, request, pk): ...
    def delete(self, request, pk): ...
```

Это даёт три операции на `/users/{pk}/` — `GET`, `PUT`, `DELETE` — и ничего для `POST`/`PATCH`, поскольку `UserDetail` их не реализует.
