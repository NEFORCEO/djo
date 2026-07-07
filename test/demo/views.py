from django.http import JsonResponse
from django.views import View


def list_users(request):
    """List all users."""
    return JsonResponse({"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Alan"}]})


def create_user(request):
    """Create a new user."""
    return JsonResponse({"id": 3, "name": "New user"}, status=201)


class UserDetail(View):
    """Retrieve, update or delete a single user by id."""

    def get(self, request, pk):
        return JsonResponse({"id": pk, "name": "Ada"})

    def put(self, request, pk):
        return JsonResponse({"id": pk, "updated": True})

    def delete(self, request, pk):
        return JsonResponse({"id": pk, "deleted": True})
