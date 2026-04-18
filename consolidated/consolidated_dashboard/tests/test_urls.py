from django.urls import resolve, reverse
from consolidated_dashboard.views import ConsolidatedDashboardView


def test_consolidated_url_resolve():
    url = reverse("consolidated-dashboard")
    resolver = resolve(url)
    assert resolver.func.view_class == ConsolidatedDashboardView
