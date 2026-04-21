# dashboard/tests/test_urls.py
from django.urls import resolve, reverse

from dashboard.views import DashboardKPIsView


def test_dashboard_kpis_url_resolves():
    url = reverse("dashboard-kpis")
    resolver = resolve(url)

    assert resolver.func.view_class == DashboardKPIsView


def test_dashboard_kpis_url_path():
    url = reverse("dashboard-kpis")

    assert url == "/api/dashboard/kpis/"
    