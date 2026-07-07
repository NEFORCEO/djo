# Request Bodies

For `POST`/`PUT`/`PATCH` operations, djo builds a `requestBody` schema in two steps: prefer a declared DRF serializer ([see DRF Serializers](drf-serializers.md)), and fall back to reading the handler's source when there isn't one.

## Without a serializer

djo scans the concrete handler for body-access markers — `request.body`, `request.POST`, `request.FILES`, `request.data`, `json.loads` — and, if any are found, extracts field names from patterns like `request.POST.get("name")` or `request.data["age"]`:

```python
def create_user(request):
    name = request.POST.get("name")
    age = request.data["age"]
    ...
```

produces:

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

Field types are always `string` in this fallback path — without a serializer or type hints, djo has no reliable way to know a field is actually numeric or boolean. If you need accurate types, declare a DRF `serializer_class` instead.

## No body access, no `requestBody`

If a handler never touches the request body, djo **omits `requestBody` entirely** rather than emitting a misleading empty `{}` schema — this was the whole point of moving past a naive "every POST has a body" assumption:

```python
def create_user(request):
    """Create a new user."""
    return JsonResponse({"id": 3, "name": "New user"}, status=201)
```

This handler never reads `request.POST`/`request.data`, so no `requestBody` shows up in Swagger UI for it — nothing to fill in, nothing misleading to guess at.

## Detected body markers

| Marker | Typical usage |
|---|---|
| `request.POST` | Classic form-encoded Django views |
| `request.data` | Django REST Framework views |
| `request.body` | Manual JSON parsing (`json.loads(request.body)`) |
| `request.FILES` | File uploads |
| `json.loads` | Manual JSON parsing, any source |
