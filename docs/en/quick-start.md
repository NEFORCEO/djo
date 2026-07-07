# Quick Start

## Install

```console
$ pip install djo
```

## Add it to `INSTALLED_APPS`

That's the entire setup — no `urls.py` edits, no extra settings required:

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

## Run your project

```console
$ python manage.py runserver
```

## Open the docs

Go to <a href="http://127.0.0.1:8000/docs" target="_blank">http://127.0.0.1:8000/docs</a>.

djo walks `ROOT_URLCONF` the moment the page is requested and builds a live OpenAPI schema from whatever it finds — every `path()`/`re_path()` entry, including ones registered by third-party apps (like `django.contrib.admin`, visible in the screenshot below):

![Swagger UI](../media/swagger.png)

Expand any operation to see path/query parameters, inferred request bodies, and response codes. Click **Try it out** to send a real request from the browser — djo forwards the CSRF cookie automatically, so POST/PUT/PATCH/DELETE work out of the box against session-authenticated views.

## Why no `urls.py` changes?

`djo.apps.DjangoAPIConfig.ready()` prepends `djo.middleware.DjangoAPIMiddleware` to `settings.MIDDLEWARE` the moment the app is loaded — `ready()` always runs during `django.setup()`, which completes before Django builds the middleware chain. The middleware then intercepts `/docs` and `/openapi.json` ahead of normal URL resolution; every other request passes straight through untouched. See **[How It Works](how-it-works.md)** for the full picture.

## Next steps

- **[Features overview](features/index.md)** — what djo infers automatically, and from where.
- **[Configuration](configuration.md)** — override the title, version, description, or the docs URLs.
- **[Demo project](demo-project.md)** — a working example you can run locally.
