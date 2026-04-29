# dashboard/tests/test_urls.py
from django.urls import resolve, reverse

from dashboard.views import (
    CostCompositionView,
    DashboardKPIsView,
    MainDashboardView,
    SummaryTableView,
)


def test_dashboard_kpis_url_resolves():
    url = reverse("dashboard-kpis")
    resolver = resolve(url)
    assert resolver.func.view_class == DashboardKPIsView


def test_dashboard_kpis_url_path():
    url = reverse("dashboard-kpis")
    assert url == "/api/dashboard/kpis/"


def test_dashboard_projects_url_resolves():
    url = reverse("dashboard-projects")
    resolver = resolve(url)
    assert resolver.func.view_class == MainDashboardView


def test_dashboard_projects_url_path():
    url = reverse("dashboard-projects")
    assert url == "/api/dashboard/projects/"


def test_dashboard_summary_url_resolves():
    url = reverse("dashboard-summary")
    resolver = resolve(url)
    assert resolver.func.view_class == SummaryTableView


def test_dashboard_summary_url_path():
    url = reverse("dashboard-summary")
    assert url == "/api/dashboard/summary/"


def test_dashboard_composition_url_resolves():
    url = reverse("dashboard-composition")
    resolver = resolve(url)
    assert resolver.func.view_class == CostCompositionView


def test_dashboard_composition_url_path():
    url = reverse("dashboard-composition")
    assert url == "/api/dashboard/composition/"
