# Как это работает

djo — это четыре небольших модуля. Никаких декораторов, никакого шага генерации кода на этапе сборки — схема заново вычисляется при каждом запросе к `/openapi.json`.

## 1. Самоустанавливающийся middleware

```python
# djo/apps.py
class DjangoAPIConfig(AppConfig):
    name = "djo"

    def ready(self) -> None:
        middleware = list(settings.MIDDLEWARE)
        if MIDDLEWARE_PATH in middleware:
            return
        try:
            index = middleware.index(SECURITY_MIDDLEWARE_PATH) + 1
        except ValueError:
            index = 0
        middleware.insert(index, MIDDLEWARE_PATH)
        settings.MIDDLEWARE = middleware
```

Django вызывает `AppConfig.ready()` ровно один раз, во время `django.setup()` — а `django.setup()` всегда завершается *до того*, как `get_wsgi_application()` / `get_asgi_application()` вызовут `load_middleware()` для построения цепочки запрос/ответ. Именно этот порядок и позволяет `djo` вставить свой middleware в `settings.MIDDLEWARE` прямо в момент импорта — просто из факта присутствия в `INSTALLED_APPS`, без единой правки `urls.py` и без ручной записи в `MIDDLEWARE`. Он ставится сразу после `SecurityMiddleware` (или в начало списка, если его нет), чтобы HTTPS-редиректы и security-заголовки покрывали и `/docs`.

## 2. Сам middleware

```python
# djo/middleware.py
class DjangoAPIMiddleware:
    def __call__(self, request):
        path = _normalize(request.path)

        if path == self.docs_url:
            return self._serve(request, self._docs)
        if path == self.openapi_url:
            return self._serve(request, self._openapi)
        return self.get_response(request)

    def _serve(self, request, handler):
        if not is_enabled():                    # DJO["ENABLED"], по умолчанию settings.DEBUG
            return self.get_response(request)
        if request.method not in ("GET", "HEAD"):
            return HttpResponseNotAllowed(("GET", "HEAD"))
        gate = get_gate()                        # необязательный колбэк DJO["GATE"]
        if gate is not None and not gate(request):
            return self.get_response(request)
        return handler(request)
```

Он выполняется у вершины цепочки и перехватывает `/docs` и `/openapi.json` раньше, чем их вообще увидит обычная резолюция URL Django — но только для безопасных методов, только когда включён, и только если `GATE` разрешает. Все остальные запросы, как и отклонённые `GATE`, проходят насквозь без изменений. Следствие: эти два пути никогда не попадают в схему как «обнаруженные» эндпоинты — они обрабатываются полностью в обход обхода URLconf.

## 3. Генерация схемы

```python
# djo/generator.py
def generate_openapi_schema() -> dict:
    for path, url_pattern in discover_endpoints():
        ...
```

`discover_endpoints()` рекурсивно обходит `get_resolver().url_patterns`, отличая `URLResolver` (вложенные `include()`) от `URLPattern` (конечные view), и превращает синтаксис маршрутов Django вида `<int:pk>` в синтаксис OpenAPI вида `{pk}`. Для каждого конечного узла djo читает:

- **Path-параметры** из `RoutePattern.converters` (пусто для `re_path()`).
- **HTTP-методы** — по тому, какие из `get`/`post`/`put`/`patch`/`delete` реализует класс view (function-based view по умолчанию — `GET`).
- **Summary и description** — из docstring хендлера: первая строка становится `summary` операции, остальное — `description`, которое Swagger UI рендерит как markdown.
- **Query-параметры**, **тело запроса/ответа**, **требования авторизации** и **коды ошибок** — каждое разобрано на своей странице в разделе [Возможности](features/index.md).

Ничто из этого не исполняет код вашего view. Тело и ошибки определяются чтением исходника конкретного хендлера через `inspect.getsource()` и сопоставлением с набором регулярных выражений; сериализаторы и классы прав доступа читаются как статические атрибуты класса.

## 4. Swagger UI

```python
# djo/swagger.py
SWAGGER_HTML = """<!DOCTYPE html>
...
<style> html, body { margin: 0; background: #ffffff; } .topbar { display: none; } </style>
...
"""
```

Единый HTML-шаблон, указывающий `swagger-ui-dist` (загружается с CDN) на `/openapi.json`, оформленный в белой/простой теме вместо тёмной темы библиотеки по умолчанию. Небольшой `requestInterceptor` читает cookie `csrftoken` и подставляет её как заголовок `X-CSRFToken` для небезопасных методов, поэтому **Try it out** работает с реальными, защищёнными CSRF view Django без какой-либо дополнительной настройки.

## Принципы дизайна

- **Интроспекция важнее аннотаций.** Если Django или DRF уже что-то знают о view (конвертеры, поля сериализатора, классы прав доступа), djo это читает — и никогда не просит повторить эту информацию в декораторе.
- **Эвристика, а не типизация.** Вывод по исходнику (query-параметры, тело запроса, коды ошибок) — это эвристика, а не гарантия. Что именно она видит и не видит — описано в примечаниях на [странице каждой возможности](features/index.md).
- **Ничего не исполняется.** За исключением вызова `__init__`/`get_fields()` у сериализатора, никакой код view или хендлера никогда не выполняется во время генерации схемы.
