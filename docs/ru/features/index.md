# Обзор возможностей

djo никогда не исполняет ваши view и ничего не отправляет по сети, чтобы построить схему. Всё определяется через **интроспекцию**: обход URL-резолвера Django, чтение атрибутов классов ваших view, и — там, где больше ничего не доступно — чтение исходного кода хендлера через `inspect.getsource()`.

| Что | Источник данных | Страница |
|---|---|---|
| Пути и HTTP-методы | `ROOT_URLCONF` / `View.as_view()` / DRF `APIView` | [Path-параметры](path-parameters.md) |
| Path-параметры | Конвертеры Django `path()` (`<int:pk>`, `<uuid:token>`, ...) | [Path-параметры](path-parameters.md) |
| Query-параметры | `request.GET.get(...)` / `request.GET[...]` в исходнике хендлера | [Query-параметры](query-parameters.md) |
| Тело запроса | `serializer_class` view, либо обращения к `request.POST` / `request.data` в исходнике | [Тело запроса](request-bodies.md) |
| Тело ответа | `serializer_class` view | [DRF-сериализаторы](drf-serializers.md) |
| Требования авторизации | `permission_classes`, `authentication_classes`, `LoginRequiredMixin` | [Схемы авторизации](security.md) |
| Коды ошибок | `status=404`, `status.HTTP_400_BAD_REQUEST`, поднятые исключения | [Коды ошибок](error-responses.md) |

## Стратегия в два уровня

Для тела запроса/ответа и авторизации djo всегда предпочитает **декларативную, статическую информацию** угадыванию:

1. Если class-based view объявляет DRF `serializer_class`, djo читает поля прямо из него — типы, `required`, `read_only`/`write_only`, `choices`. Это точно работает для любого хендлера независимо от того, что реально делает тело функции.
2. Иначе djo переключается на лёгкое чтение исходника конкретного хендлера через регулярные выражения — ищутся паттерны обращения к `request.GET`/`request.POST`/`request.data`. Код хендлера при этом никогда не исполняется.

То же правило действует и для авторизации: `permission_classes`/`authentication_classes` (DRF) или наличие `LoginRequiredMixin` (обычный Django) читаются прямо с класса — ничего не создаётся и не вызывается.

!!! note "Function-based view всегда по умолчанию GET"
    Django не даёт встроенного способа узнать, какие HTTP-методы принимает обычная функция-view — только class-based view декларируют методы-хендлеры (`get`, `post`, ...), которые djo может перечислить. Если нужна точная детекция методов для функции, оберните её в class-based view или DRF `@api_view`.
