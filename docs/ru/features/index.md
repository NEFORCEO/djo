# Обзор возможностей

djo никогда не исполняет ваши view и ничего не отправляет по сети, чтобы построить схему. Всё определяется через **интроспекцию**: обход URL-резолвера Django, чтение атрибутов классов ваших view, и — там, где больше ничего не доступно — чтение исходного кода хендлера через `inspect.getsource()`.

| Что | Источник данных | Страница |
|---|---|---|
| Пути и HTTP-методы | `ROOT_URLCONF` / `View.as_view()` / DRF `APIView` | [Path-параметры](path-parameters.md) |
| Path-параметры | Конвертеры Django `path()` (`<int:pk>`, `<uuid:token>`, ...) | [Path-параметры](path-parameters.md) |
| Query-параметры | Типизированная сигнатура хендлера, либо `request.GET.get(...)` / `request.GET[...]` в исходнике | [Query-параметры](query-parameters.md) |
| Заголовки и куки | Обращения к `request.headers`/`request.COOKIES` в исходнике | [Заголовки и куки](headers-cookies.md) |
| Тело запроса | `serializer_class`, типизированная сигнатура хендлера, обращения к `request.POST`/`request.data`, либо `request.FILES` для загрузки файлов | [Тело запроса](request-bodies.md) |
| Тело ответа и примеры | `serializer_class`, либо литерал `return JsonResponse({...})` в исходнике (реальные значения литералов становятся `example`) | [Схема ответа](response-schema.md) |
| Summary и description | docstring хендлера — первая строка как summary, остальное как markdown-описание | [Как это работает](../how-it-works.md) |
| Требования авторизации | `permission_classes`, `authentication_classes`, `LoginRequiredMixin` | [Схемы авторизации](security.md) |
| Коды ошибок | `status=404`, `status.HTTP_400_BAD_REQUEST`, поднятые исключения | [Коды ошибок](error-responses.md) |

## Многоуровневая стратегия

Для тела запроса/ответа и авторизации djo всегда предпочитает **декларативную, статическую информацию** угадыванию:

1. Если class-based view объявляет DRF `serializer_class`, djo читает поля прямо из него — типы, `required`, `read_only`/`write_only`, `choices`. Это точно работает для любого хендлера независимо от того, что реально делает тело функции.
2. Иначе, если в самой сигнатуре хендлера есть типовые аннотации у параметров помимо `request`/`self`/path-параметров, djo читает их напрямую — см. [Query-параметры](query-parameters.md).
3. Иначе djo переключается на лёгкое, эвристическое чтение исходника конкретного хендлера — регулярные выражения для `request.GET`/`request.POST`/`request.data`, и обход AST в поисках литерала `return JsonResponse({...})`. Код хендлера при этом никогда не исполняется.

То же правило действует и для авторизации: `permission_classes`/`authentication_classes` (DRF) или наличие `LoginRequiredMixin` (обычный Django) читаются прямо с класса — ничего не создаётся и не вызывается.

!!! note "Function-based view всегда по умолчанию GET"
    Django не даёт встроенного способа узнать, какие HTTP-методы принимает обычная функция-view — только class-based view декларируют методы-хендлеры (`get`, `post`, ...), которые djo может перечислить. Если нужна точная детекция методов для функции, оберните её в class-based view или DRF `@api_view`.
