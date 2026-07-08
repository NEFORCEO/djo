# Тело запроса

Для операций `POST`/`PUT`/`PATCH` djo строит схему `requestBody` в три шага, каждый в приоритете над следующим: объявленный DRF-сериализатор (см. [DRF-сериализаторы](drf-serializers.md)), типизированная сигнатура хендлера, и, наконец, резервное чтение исходника хендлера.

## Типизированная сигнатура хендлера

Дополнительные параметры хендлера с обычной типовой аннотацией (см. [Query-параметры](query-parameters.md) — там полный список поддерживаемых типов) становятся полями тела запроса для `POST`/`PUT`/`PATCH` вместо query-параметров:

```python
def create_user(request, name: str, age: int, active: bool = True):
    ...
```

даёт:

```json
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age": { "type": "integer" },
    "active": { "type": "boolean" }
  },
  "required": ["name", "age"]
}
```

Параметр считается `required`, если у него нет значения по умолчанию — точно как в обычном вызове Python-функции.

!!! warning "Django не привязывает эти значения за вас"
    Диспетчер Django вызывает view только с `request` плюс тем, что захватил конвертер `path()` — он никогда не подставляет дополнительные параметры из тела запроса. Обязательный параметр без значения по умолчанию вызовет `TypeError: missing N required positional arguments` в момент обращения к view, поэтому в реальном хендлере *каждому* дополнительному параметру нужно значение по умолчанию (соответствующее его типу) и самостоятельное чтение реального значения — обычно из `request.data`/`request.POST`:
    ```python
    def create_user(request, name: str = "", age: int = 0, active: bool = True):
        name = request.data.get("name", name)
        age = int(request.data.get("age", age))
        ...
    ```
    Аннотация питает только схему OpenAPI — она не настраивает привязку данных.

## Без сериализатора и типизированной сигнатуры

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

В этом резервном варианте типы полей всегда `string` — без сериализатора или типизированной сигнатуры у djo нет надёжного способа узнать, что поле на самом деле числовое или булево. Если нужны точные типы — объявите DRF `serializer_class` или добавьте типовые аннотации к параметрам хендлера.

## Загрузка файлов

Если хендлер читает `request.FILES`, djo документирует поле как бинарную загрузку и переключает весь `requestBody` на `multipart/form-data` — файловые поля и обычные поля из `request.POST` объединяются в одну form-схему:

```python
class AvatarUpload(View):
    """
    Upload a user avatar.

    Accepts a multipart form with the image file plus an optional caption.
    The file is stored and its URL is returned.
    """

    def post(self, request):
        avatar = request.FILES.get("avatar")
        caption = request.POST.get("caption", "")
        return JsonResponse({"filename": avatar.name if avatar else "", "caption": caption}, status=201)
```

Развёрнуто в Swagger UI — обратите внимание на выбор файла для `avatar` и многострочный docstring, отрендеренный как markdown-описание операции:

![Загрузка файла](../../media/file-upload.png)

`request.FILES["avatar"]` (доступ через `[]`) работает так же, как `.get(...)` — любого из них достаточно, чтобы пометить поле как `{"type": "string", "format": "binary"}`.

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
