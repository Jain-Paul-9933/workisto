from django.urls import path

from .views import (
    CsrfView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    SearchTokenView,
)

app_name = "accounts"

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="csrf"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/search-token/", SearchTokenView.as_view(), name="search-token"),
    path("me/", MeView.as_view(), name="me"),
]
