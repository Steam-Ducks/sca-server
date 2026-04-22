# dashboard/urls.py
from django.urls import path

from dashboard.views import DashboardKPIsView

urlpatterns = [
    path("dashboard/kpis/", DashboardKPIsView.as_view(), name="dashboard-kpis"),
]
