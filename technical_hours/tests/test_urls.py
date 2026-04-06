from django.urls import resolve, reverse

from technical_hours.views import TechnicalHoursTableView


def test_technical_hours_url_resolve():
    url = reverse("technical-hours-table")
    resolver = resolve(url)

    assert resolver.func.view_class == TechnicalHoursTableView
