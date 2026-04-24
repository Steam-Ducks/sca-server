from django.urls import path
from main_dashboard.views import MainDashboardView

urlpatterns = [
    path("main-dashboard/", MainDashboardView.as_view(), name="main-dashboard"),
]
