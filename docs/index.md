<p align="center">
  <img src="media/django-icon.png" style="border-radius:20px; width:120">
</p>
<p align="center">
    <em>Drop-in interactive API docs for Django — Swagger UI, FastAPI-style, with zero decorators and zero extra dependencies.</em>
</p>
<p align="center">
<a href="https://github.com/NEFORCEO/djo/actions/workflows/publish.yml" target="_blank">
    <img src="https://github.com/NEFORCEO/djo/actions/workflows/publish.yml/badge.svg" alt="Publish">
</a>
<a href="https://pypi.org/project/djo" target="_blank">
    <img src="https://img.shields.io/pypi/v/djo?color=%2334D058&label=pypi%20package" alt="Package version">
</a>
<a href="https://pypi.org/project/djo" target="_blank">
    <img src="https://img.shields.io/pypi/dm/djo?color=%2334D058&label=downloads" alt="Monthly downloads">
</a>
</p>
<p align="center">
<a href="https://www.python.org/" target="_blank">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/NEFORCEO/djo/master/docs/endpoints/python.json" alt="Python">
</a>
<a href="https://www.djangoproject.com/" target="_blank">
    <img src="https://img.shields.io/badge/django-5.2%2B-0C4B33" alt="Django">
</a>
<a href="https://github.com/NEFORCEO/djo/blob/master/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/NEFORCEO/djo?color=%2334D058" alt="License">
</a>
</p>
<p align="center">
<a href="https://github.com/NEFORCEO/djo" target="_blank">
    <img src="https://img.shields.io/github/stars/NEFORCEO/djo?style=social" alt="GitHub Stars">
</a>
</p>

---

**Documentation**: <a href="https://djo.readthedocs.io" target="_blank">https://djo.readthedocs.io</a>

**Source Code**: <a href="https://github.com/NEFORCEO/djo" target="_blank">https://github.com/NEFORCEO/djo</a>

---

djo turns any Django project into a self-documenting API. Add one line to `INSTALLED_APPS` and a full Swagger UI shows up at `/docs` — no urls.py edits, no serializers, no decorators on your views. It walks your project's own `urlpatterns` and builds the OpenAPI schema from what it finds.

The key features are:

* **Zero config** — the only thing you touch is `INSTALLED_APPS`. No `urls.py` changes, no middleware to wire up by hand.
* **Automatic** — paths, path parameters and HTTP methods are all inferred by walking the URLconf and the views it points to. Nothing to decorate, nothing to register.
* **Typed path params** — `<int:pk>`, `<uuid:token>`, `<slug:handle>` are mapped to real OpenAPI types straight from Django's own path converters.
* **Query params** — `request.GET.get("page", 1)` / `request.GET["tag"]` style access is picked up automatically, with type and required-ness inferred from how it's read.
* **Smart request bodies** — instead of a blank `{}`, djo reads a handler's source for `request.POST.get(...)` / `request.data[...]` style access and pre-fills the example with the fields it actually uses.
* **DRF serializer aware** — if a view declares `serializer_class`, djo reads the real fields straight off it instead of guessing.
* **Auth-aware** — `permission_classes`, `authentication_classes` and `LoginRequiredMixin` are detected automatically and surfaced as a Swagger **Authorize** button.
* **Error responses** — status codes referenced via `status=404` or raised via `Http404`/DRF exceptions are added to the schema automatically.
* **Interactive** — "Try it out" works against your real endpoints out of the box; the CSRF cookie is forwarded automatically for unsafe methods.
* **No extra dependencies** — pure Django. No Pydantic, no DRF required (though it plays nicely with DRF views if you have them).

---

## Requirements

Python 3.10+, Django 5.2+.

## Installation

```console
$ pip install djo
```

## Example

Add `"djo"` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "djo",
]
```

That's it. Run your project as usual:

```console
$ python manage.py runserver
```

### Check it

Go to <a href="http://127.0.0.1:8000/docs" target="_blank">http://127.0.0.1:8000/docs</a>.

You will see the automatic interactive API documentation, generated straight from your `urlpatterns` — grouped by tag, with an **Authorize** button whenever a view needs auth:

![Swagger UI](media/swagger.png)

Expand any route to inspect parameters, request bodies and responses. Click **Try it out** to execute the request for real and see the actual response — session auth and CSRF are handled for you.

Continue to the **[Quick Start](en/quick-start.md)** ([Russian](ru/quick-start.md)) for a full walkthrough, or jump straight into the **[Features](en/features/index.md)** reference.

## License

This project is licensed under the terms of the <a href="https://github.com/NEFORCEO/djo/blob/master/LICENSE" target="_blank">MIT license</a>.
