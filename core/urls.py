from django.urls import include, path

from core.views import health_check, test_log

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("test-log/", test_log, name="test-log"),
]