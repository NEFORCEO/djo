# DRF-сериализаторы

djo не имеет зависимостей — Django REST Framework ему не требуется — но если он установлен, а view объявляет `serializer_class`, djo использует его для построения точных схем запроса и ответа прямо из объявленных полей сериализатора, вместо угадывания по исходнику.

```python
from rest_framework import serializers
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated


class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    in_stock = serializers.BooleanField(default=True)


class ProductListCreateView(ListCreateAPIView):
    """List or create products."""

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
```

Развёрнутый `POST /products/` в Swagger UI:

![DRF-сериализатор](../../media/drf-serializer.png)

Обратите внимание, что произошло автоматически:

- У `id` стоит `read_only=True` в сериализаторе, поэтому оно **исключено из тела запроса**, но присутствует в схеме ответа.
- У `name` и `price` нет ни значения по умолчанию, ни `required=False`, поэтому они помечены как `"required": ["name", "price"]`.
- Типы взяты прямо из классов полей — `IntegerField` → `integer`, `DecimalField` → `number`, `BooleanField` → `boolean` — а не угаданы по исходнику.
- `permission_classes = [IsAuthenticated]` привёл к появлению замочка и требования `Authorize` — см. [Схемы авторизации](security.md).
- `ListCreateAPIView` (DRF `CreateModelMixin`) заставил djo документировать ответ `POST` как `201 Created` вместо стандартного `200`, а ответ `GET` — как `array` из схемы сериализатора (DRF `ListModelMixin`).

## Соответствие типов полей DRF

| Поле DRF | Схема OpenAPI |
|---|---|
| `BooleanField`, `NullBooleanField` | `{"type": "boolean"}` |
| `IntegerField` | `{"type": "integer"}` |
| `FloatField`, `DecimalField` | `{"type": "number"}` |
| `CharField`, `SlugField` | `{"type": "string"}` |
| `EmailField` | `{"type": "string", "format": "email"}` |
| `URLField` | `{"type": "string", "format": "uri"}` |
| `UUIDField` | `{"type": "string", "format": "uuid"}` |
| `DateField` | `{"type": "string", "format": "date"}` |
| `DateTimeField` | `{"type": "string", "format": "date-time"}` |
| `ChoiceField` | `{"type": "string", "enum": [...]}` — заполняется из `field.choices` |
| `ListField` | `{"type": "array", "items": {"type": "string"}}` |
| `PrimaryKeyRelatedField` | `{"type": "integer"}` |
| всё остальное | `{"type": "string"}` (по умолчанию) |

`help_text` поля, если он задан, переносится прямо в `"description"` схемы:

```python
email = serializers.EmailField(help_text="Used for login and notifications.")
```

даёт `{"type": "string", "format": "email", "description": "Used for login and notifications."}`.

## Поля запроса и ответа

djo строит из одного сериализатора две разные схемы:

| Направление | Исключает | Помечает `required` |
|---|---|---|
| Запрос (`requestBody`) | поля `read_only` | да, из `field.required` |
| Ответ (тело `200`/`201`) | поля `write_only` | нет — представление не валидируется |

## Что никогда не вызывается

Читается только **статический** атрибут `serializer_class`. djo никогда не вызывает `get_serializer_class()` — проекты часто переопределяют его логикой, зависящей от `self.request` или `self.action`, а вызывать это вне реального цикла запрос/ответ небезопасно. Если у view объявлен только `get_serializer_class()`, djo переключается на вывод по исходнику, описанный в разделе [Тело запроса](request-bodies.md).
