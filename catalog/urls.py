from django.urls import path

from .views import ServiceCategoryDetailView, ServiceCategoryListView

app_name = "catalog"

urlpatterns = [
    path("categories/", ServiceCategoryListView.as_view(), name="category-list"),
    path(
        "categories/<slug:slug>/",
        ServiceCategoryDetailView.as_view(),
        name="category-detail",
    ),
]
