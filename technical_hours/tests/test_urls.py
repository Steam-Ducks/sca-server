from django.urls import resolve, reverse

from technical_hours.views import TechnicalHoursTablePeriodoView, TechnicalHoursTableView


def test_technical_hours_url_resolve():
    url = reverse("technical-hours-table")
    resolver = resolve(url)
    assert resolver.func.view_class == TechnicalHoursTableView


def test_technical_hours_periodo_url_resolve():
    url = reverse("technical-hours-table-periodo", kwargs={"periodo": "2024-03"})
    resolver = resolve(url)
    assert resolver.func.view_class == TechnicalHoursTablePeriodoView
