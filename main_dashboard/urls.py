from django.urls import path

from main_dashboard.views import CostCompositionView, MainDashboardView, SummaryTableView

urlpatterns = [
    path("main-dashboard/", MainDashboardView.as_view(), name="main-dashboard"),
    path(
        "main-dashboard/summary/",
        SummaryTableView.as_view(),
        name="main-dashboard-summary",
    ),
    path(
        "main-dashboard/composition/",
        CostCompositionView.as_view(),
        name="main-dashboard-composition",
    ),
]
