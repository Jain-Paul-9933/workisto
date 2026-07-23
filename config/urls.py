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
    path("api/", include("catalog.urls")),
    path("api/", include("providers.urls")),
    path("api/", include("booking.urls")),
    path("api/", include("reviews.urls")),
    path("api/", include("pricing.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("chat.urls")),
    # More API slices get mounted here as we build them.
]
