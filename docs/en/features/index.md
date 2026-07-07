# Features Overview

djo never executes your views and never sends anything over the network to build the schema. Everything is inferred by **introspection**: walking Django's URL resolver, reading class attributes off your views, and — where nothing else is available — reading the handler's own source with `inspect.getsource()`.

| What | Inferred from | Page |
|---|---|---|
| Paths & HTTP methods | `ROOT_URLCONF` / `View.as_view()` / DRF `APIView` | [Path Parameters](path-parameters.md) |
| Path parameters | Django's `path()` converters (`<int:pk>`, `<uuid:token>`, ...) | [Path Parameters](path-parameters.md) |
| Query parameters | A typed handler signature, or `request.GET.get(...)` / `request.GET[...]` in source | [Query Parameters](query-parameters.md) |
| Request bodies | A `serializer_class`, a typed handler signature, or `request.POST` / `request.data` access in source | [Request Bodies](request-bodies.md) |
| Response bodies | A `serializer_class`, or a literal `return JsonResponse({...})` in source | [Response Schema](response-schema.md) |
| Auth requirements | `permission_classes`, `authentication_classes`, `LoginRequiredMixin` | [Security Schemes](security.md) |
| Error responses | `status=404`, `status.HTTP_400_BAD_REQUEST`, raised exceptions | [Error Responses](error-responses.md) |

## The layered strategy

For request/response bodies and auth, djo always prefers **declared, static information** over guessing:

1. If a class-based view declares a DRF `serializer_class`, djo reads its fields directly — types, `required`, `read_only`/`write_only`, `choices`. This is accurate for any handler, regardless of what the function body actually does.
2. Otherwise, if the handler's own signature carries type annotations on parameters beyond `request`/`self`/path parameters, djo reads those directly — see [Typed handler signatures](query-parameters.md#typed-handler-signatures).
3. Otherwise, djo falls back to a light, best-effort read of the concrete handler's source — regex for `request.GET`/`request.POST`/`request.data` access, and an `ast` walk for a literal `return JsonResponse({...})`. No handler code is ever executed.

The same rule applies to security: a view's `permission_classes`/`authentication_classes` (DRF) or presence of `LoginRequiredMixin` (plain Django) are read directly off the class — nothing is instantiated, nothing is called.

!!! note "Function-based views only ever default to GET"
    Django exposes no built-in signal for which HTTP methods a plain function view accepts — only class-based views declare handler methods (`get`, `post`, ...) that djo can enumerate. If you need accurate method detection for a function view, wrap it in a class-based view or a DRF `@api_view`.
