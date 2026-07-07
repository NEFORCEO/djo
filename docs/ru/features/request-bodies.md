# Тело запроса

Для операций `POST`/`PUT`/`PATCH` djo строит схему `requestBody` в два шага: сначала пытается использовать объявленный DRF-сериализатор (см. [DRF-сериализаторы](drf-serializers.md)), а если его нет — переключается на чтение исходника хендлера.

## Без сериализатора

djo сканирует конкретный хендлер на маркеры обращения к телу запроса — `request.body`, `request.POST`, `request.FILES`, `request.data`, `json.loads` — и если находит хотя бы один, извлекает имена полей из паттернов вида `request.POST.get("name")` или `request.data["age"]`:

```python
def create_user(request):
    name = request.POST.get("name")
    age = request.data["age"]
    ...
```

даёт:

```json
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "string" }
  },
  "example": { "name": "", "age": "" }
}
```

В этом резервном варианте типы полей всегда `string` — без сериализатора или типовых аннотаций у djo нет надёжного способа узнать, что поле на самом деле числовое или булево. Если нужны точные типы — объявите DRF `serializer_class`.

## Нет обращения к телу — нет `requestBody`

Если хендлер вообще не трогает тело запроса, djo **полностью пропускает `requestBody`**, а не выводит вводящую в заблуждение пустую схему `{}` — именно в этом был смысл отказа от наивного предположения "у каждого POST есть тело":

```python
def create_user(request):
    """Create a new user."""
    return JsonResponse({"id": 3, "name": "New user"}, status=201)
```

Этот хендлер никогда не читает `request.POST`/`request.data`, поэтому для него в Swagger UI не появится `requestBody` — нечего заполнять, нечего вводящее в заблуждение угадывать.

## Определяемые маркеры тела запроса

| Маркер | Типичное использование |
|---|---|
| `request.POST` | Классические form-encoded view в Django |
| `request.data` | View Django REST Framework |
| `request.body` | Ручной разбор JSON (`json.loads(request.body)`) |
| `request.FILES` | Загрузка файлов |
| `json.loads` | Ручной разбор JSON, любой источник |
