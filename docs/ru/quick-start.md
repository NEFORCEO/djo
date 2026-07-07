# Быстрый старт

## Установка

```console
$ pip install djo
```

## Добавьте в `INSTALLED_APPS`

Это вся настройка целиком — никаких правок `urls.py`, никаких дополнительных настроек:

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "djo",
]
```

## Запустите проект

```console
$ python manage.py runserver
```

## Откройте документацию

Перейдите на <a href="http://127.0.0.1:8000/docs" target="_blank">http://127.0.0.1:8000/docs</a>.

djo обходит `ROOT_URLCONF` в момент запроса страницы и строит живую OpenAPI-схему из всего, что найдёт — каждую запись `path()`/`re_path()`, включая маршруты сторонних приложений (например, `django.contrib.admin`, как на скриншоте ниже):

![Swagger UI](../media/swagger.png)

Разверните любую операцию, чтобы увидеть path/query-параметры, автоматически определённое тело запроса и коды ответов. Нажмите **Try it out**, чтобы отправить настоящий запрос прямо из браузера — djo сам подставляет CSRF-cookie, поэтому POST/PUT/PATCH/DELETE работают из коробки против view с сессионной аутентификацией.

## Почему не нужно трогать `urls.py`

`djo.apps.DjangoAPIConfig.ready()` добавляет `djo.middleware.DjangoAPIMiddleware` в начало `settings.MIDDLEWARE` в момент загрузки приложения — `ready()` всегда выполняется во время `django.setup()`, а это происходит раньше, чем Django строит цепочку middleware. Именно этот порядок и позволяет всему пакету работать от одной записи в `INSTALLED_APPS`. Подробности — в разделе **[Как это работает](how-it-works.md)**.

## Дальше

- **[Обзор возможностей](features/index.md)** — что именно djo определяет автоматически и откуда берёт данные.
- **[Конфигурация](configuration.md)** — переопределение заголовка, версии, описания и путей документации.
- **[Демо-проект](demo-project.md)** — рабочий пример, который можно запустить локально.
