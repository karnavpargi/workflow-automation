"""Root URL configuration; app routers are included per app."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/", include("onboarding.urls")),
    path("api/", include("invoices.urls")),
    path("api/", include("followups.urls")),
]
