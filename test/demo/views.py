from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
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


def search_users(request):
    """Search users by name."""
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    return JsonResponse({"query": query, "page": page, "results": []})


def get_user_or_404(request, pk):
    """Look up a single user, or 404 if it doesn't exist."""
    if pk != 1:
        raise Http404("User not found")
    return JsonResponse({"id": pk, "name": "Ada"})


class ProtectedUserList(LoginRequiredMixin, View):
    """List users — requires an authenticated session."""

    def get(self, request):
        return JsonResponse({"users": [{"id": 1, "name": "Ada"}]})
