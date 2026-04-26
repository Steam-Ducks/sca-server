from django.urls import path

from main_dashboard.views import MainDashboardView, SummaryTableView

urlpatterns = [
    path("main-dashboard/", MainDashboardView.as_view(), name="main-dashboard"),
    path(
        "main-dashboard/summary/",
        SummaryTableView.as_view(),
        name="main-dashboard-summary",
    ),
]
