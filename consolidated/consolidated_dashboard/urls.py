from django.urls import path
from consolidated.consolidated_dashboard.views import (
    ConsolidatedDashboardView,
    ConsolidatedDashboardPeriodoView,
)

urlpatterns = [
    path(
        "consolidated/",
        ConsolidatedDashboardView.as_view(),
        name="consolidated-dashboard",
    ),
    path(
        "consolidated/periodo/<str:periodo>/",
        ConsolidatedDashboardPeriodoView.as_view(),
        name="consolidated-dashboard-periodo",
    ),
]
