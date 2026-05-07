from django.urls import path

from core.views import health_check, status_view

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("status/", status_view, name="status"),
]
