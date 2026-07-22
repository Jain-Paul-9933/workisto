from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    """Trivial liveness probe — also proves the stack booted end-to-end."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/", include("accounts.urls")),
    # More API slices get mounted here as we build them.
]
