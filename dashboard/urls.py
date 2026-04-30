# dashboard/urls.py
from django.urls import path

from dashboard.views import (
    CostCompositionView,
    DashboardKPIsView,
    MainDashboardView,
    SummaryTableView,
    TopProjectsView,
)

urlpatterns = [
    path("dashboard/kpis/", DashboardKPIsView.as_view(), name="dashboard-kpis"),
    path("dashboard/projects/", MainDashboardView.as_view(), name="dashboard-projects"),
    path("dashboard/summary/", SummaryTableView.as_view(), name="dashboard-summary"),
    path(
        "dashboard/composition/",
        CostCompositionView.as_view(),
        name="dashboard-composition",
    ),
    path(
        "dashboard/top-projects/",
        TopProjectsView.as_view(),
        name="dashboard-top-projects",
    ),
]
