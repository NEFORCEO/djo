# Демо-проект

В репозитории есть обычный, стандартный Django-проект в [`test/`](https://github.com/NEFORCEO/djo/tree/master/test) — создан через `django-admin startproject demo .`, с `djo`, добавленным в `INSTALLED_APPS`, и несколькими view, демонстрирующими каждую возможность. Никакой специальной настройки, никакого кастомного `manage.py`.

```console
$ git clone https://github.com/NEFORCEO/djo.git
$ cd djo
$ pip install -e .
$ cd test
$ python manage.py runserver
```

Затем откройте `http://127.0.0.1:8000/docs`.

## Что внутри

| Эндпоинт | Демонстрирует |
|---|---|
| `GET /users/` | Обычная function-based view без параметров. |
| `GET /users/create/` | Ответ `201 Created`, определённый из явного `status=201`. |
| `GET /users/search/` | [Query-параметры](features/query-parameters.md) — `q` (строка, опционально) и `page` (число, опционально). |
| `GET /users/lookup/{pk}/` | [Path-параметры](features/path-parameters.md) плюс определённый `404` из `raise Http404`. |
| `GET /users/protected/` | [Схемы авторизации](features/security.md) — `LoginRequiredMixin`, показан замочком и кнопкой Authorize. |
| `GET`, `PUT`, `DELETE /users/{pk}/` | Class-based view (`django.views.View`), реализующий три метода из пяти возможных. |

Все хендлеры намеренно простые заглушки, возвращающие готовые данные через `JsonResponse` — суть демо в сгенерированной схеме, а не в реальном бэкенде. `PUT`/`DELETE` на `/users/{pk}/` ничего не сохраняют, поэтому повторные вызовы всегда «успешны» — это ожидаемое поведение демо, а не баг djo.

## Пример с DRF (не входит по умолчанию)

Скриншот из раздела [DRF-сериализаторы](features/drf-serializers.md) был получен тем же способом, с помощью временного view вроде этого — установите `djangorestframework`, добавьте `"rest_framework"` в `INSTALLED_APPS` и добавьте:

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

Этот пример не входит в поставляемый демо-проект — именно для того, чтобы демо оставалось без лишних зависимостей: сам djo никогда не требует DRF (см. [DRF-сериализаторы](features/drf-serializers.md)).
