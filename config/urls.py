from django.contrib import admin
from django.urls import include, path
from django_prometheus import exports
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("metrics", exports.ExportToDjangoView, name="prometheus-metrics"),
    path("api/", include("core.urls")),
    path("api/", include("users.urls")),
    path("api/", include("materials.urls")),
    path("api/", include("technical_hours.urls")),
    path("api/", include("consolidated.consolidated_dashboard.urls")),
    path("api/", include("dashboard.urls")),
    path("api/", include("costs.urls")),
    path("api/", include("budget.urls")),
    path("api/", include("imports.urls")),
    path("api/monitoring/", include("monitoring.urls")),
    path("api/", include("audit.urls")),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
