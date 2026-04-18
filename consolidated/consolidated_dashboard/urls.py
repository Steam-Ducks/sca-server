from django.urls import path

from consolidated.consolidated_dashboard.views import ConsolidatedDashboardView

urlpatterns = [
    path(
        "consolidated/",
        ConsolidatedDashboardView.as_view(),
        name="consolidated-dashboard",
    ),
]
