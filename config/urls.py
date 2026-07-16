from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(_request):
    """Trivial liveness probe — also proves the stack booted end-to-end."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    # API routes get mounted here as we build each feature slice.
]
