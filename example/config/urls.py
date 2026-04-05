"""
URL configuration for the example project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Midtrans API endpoints
    path("midtrans/api/", include("django_midtrans.urls")),

    # Example shop app
    path("", include("shop.urls")),

    # DRF browsable API auth
    path("api-auth/", include("rest_framework.urls")),
]
