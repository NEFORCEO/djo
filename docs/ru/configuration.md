# Конфигурация

Всё опционально — djo работает из коробки с разумными значениями по умолчанию. Переопределить заголовок, версию, описание или сами пути документации можно через словарь `DJO` в `settings.py`:

```python
DJO = {
    "TITLE": "My API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Internal API for the mobile app.",
    "DOCS_URL": "/docs",
    "OPENAPI_URL": "/openapi.json",
}
```

| Ключ | По умолчанию | Описание |
|---|---|---|
| `TITLE` | `"Django API"` | Отображается в заголовке Swagger UI и в `info.title`. |
| `VERSION` | `"1.0.0"` | Строка версии рядом с заголовком, и `info.version`. |
| `DESCRIPTION` | *(нет)* | Markdown-описание в `info.description`. Полностью опускается, если не задано. |
| `DOCS_URL` | `"/docs"` | Путь, на котором отдаётся страница Swagger UI. |
| `OPENAPI_URL` | `"/openapi.json"` | Путь, на котором отдаётся сырая JSON-схема OpenAPI 3.0. |
| `ENABLED` | `settings.DEBUG` | Главный выключатель обоих эндпоинтов. Если ложно — djo ведёт себя так, будто не установлен. |
| `GATE` | *(нет)* | Callable или строка-путь импорта, `f(request) -> bool`. Вызывается на каждый запрос документации; ложный результат скрывает её. |
| `SWAGGER_CSS_URL` | CDN jsDelivr | URL таблицы стилей для страницы Swagger UI. |
| `SWAGGER_JS_URL` | CDN jsDelivr | URL `swagger-ui-bundle.js`. |
| `SWAGGER_PRESET_JS_URL` | CDN jsDelivr | URL `swagger-ui-standalone-preset.js`. |
| `SWAGGER_CSS_SRI` / `SWAGGER_JS_SRI` / `SWAGGER_PRESET_JS_SRI` | зафиксированный `sha512` | Хэш Subresource Integrity для каждого ресурса. Автоматически убирается, если переопределён соответствующий URL. |

## Кастомный путь документации

```python
DJO = {"DOCS_URL": "/api/docs", "OPENAPI_URL": "/api/openapi.json"}
```

Middleware сравнивает путь запроса (ведущие/завершающие слэши нормализуются) с этими двумя значениями до того, как передать запрос дальше по обычной цепочке резолюции URL — так что можно выбрать любой путь, не конфликтующий с существующими маршрутами. Отдаются только `GET` и `HEAD`; остальные методы получают `405 Method Not Allowed`.

## Включение в продакшене

Оба эндпоинта раскрывают весь контур API — пути, предполагаемые тела запросов, требования авторизации, коды ошибок. `ENABLED` по умолчанию равен `settings.DEBUG`, так что обычная установка не опубликует это на проде случайно. Включайте явно, желательно за собственной проверкой доступа:

```python
DJO = {
    "ENABLED": True,
    "GATE": "myapp.docs.is_staff",
}
```

```python
# myapp/docs.py
def is_staff(request):
    return request.user.is_authenticated and request.user.is_staff
```

`GATE` вызывается на каждый запрос к `DOCS_URL` / `OPENAPI_URL`; при ложном результате djo возвращает запрос в обычную резолюцию URL (как правило, 404).

## Размещение middleware

`DjangoAPIConfig.ready()` вставляет middleware сразу после `django.middleware.security.SecurityMiddleware` (или в начало списка, если его нет), чтобы `SECURE_SSL_REDIRECT`, HSTS и прочие security-заголовки применялись и к `/docs`.

## Самостоятельный хостинг Swagger UI

CSS/JS Swagger UI по умолчанию берутся из сборки jsDelivr с зафиксированной версией и хэшами Subresource Integrity. Для offline или строгого CSP укажите свои копии `swagger-ui-dist`:

```python
DJO = {
    "SWAGGER_CSS_URL": "/static/swagger-ui/swagger-ui.css",
    "SWAGGER_JS_URL": "/static/swagger-ui/swagger-ui-bundle.js",
    "SWAGGER_PRESET_JS_URL": "/static/swagger-ui/swagger-ui-standalone-preset.js",
}
```

Переопределение URL убирает встроенный SRI-хэш для этого ресурса (он не совпал бы с другим файлом). Передайте рядом `SWAGGER_CSS_SRI` / `SWAGGER_JS_SRI` / `SWAGGER_PRESET_JS_SRI`, чтобы сохранить проверку целостности для своих файлов.
