from django.urls import path

from core.views import health_check, test_log, receive_log, receive_metric

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("test-log/", test_log, name="test-log"),
    path("logs/", receive_log),
    path("metrics/", receive_metric),
]
