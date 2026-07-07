# Demo Project

The repo ships a plain, standard Django project under [`test/`](https://github.com/NEFORCEO/djo/tree/master/test) — created with `django-admin startproject demo .`, with `djo` added to `INSTALLED_APPS` and a handful of views wired up to demonstrate each feature. No special setup, no custom `manage.py`.

```console
$ git clone https://github.com/NEFORCEO/djo.git
$ cd djo
$ pip install -e .
$ cd test
$ python manage.py runserver
```

Then open `http://127.0.0.1:8000/docs`.

## What's in it

| Endpoint | Demonstrates |
|---|---|
| `GET /users/` | A plain function view, no parameters. |
| `GET /users/create/` | A `201 Created` response inferred from an explicit `status=201`. |
| `GET /users/search/` | [Query parameters](features/query-parameters.md) — `q` (string, optional) and `page` (integer, optional). |
| `GET /users/lookup/{pk}/` | [Path parameters](features/path-parameters.md) plus an inferred `404` from a `raise Http404`. |
| `GET /users/protected/` | [Security schemes](features/security.md) — `LoginRequiredMixin`, shown with a lock icon and the Authorize button. |
| `GET`, `PUT`, `DELETE /users/{pk}/` | A class-based view (`django.views.View`) exposing three of five possible methods. |

All the handlers are intentionally simple stubs returning canned `JsonResponse` data — the point of the demo is the generated schema, not a real backend. `PUT`/`DELETE` on `/users/{pk}/` don't persist anything, so calling them repeatedly always "succeeds" — that's expected demo behavior, not a djo bug.

## DRF example (not included by default)

The [DRF Serializers](features/drf-serializers.md) screenshot was generated the same way, using a temporary view like this — install `djangorestframework`, add `"rest_framework"` to `INSTALLED_APPS`, and add:

```python
# demo/views.py
from rest_framework import serializers
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    in_stock = serializers.BooleanField(default=True)


class ProductListCreateView(ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
```

```python
# demo/urls.py
path("products/", ProductListCreateView.as_view()),
```

It isn't part of the shipped demo project, precisely so the demo stays dependency-free — djo itself never requires DRF (see [DRF Serializers](features/drf-serializers.md)).
