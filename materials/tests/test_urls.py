from django.urls import resolve, reverse

from materials.views import (
    MaterialsIndicatorsView,
    MaterialsTablePeriodoView,
    MaterialsTableView,
)


def test_materials_table_url_resolve():
    url = reverse("materials-table")
    resolver = resolve(url)

    assert resolver.func.view_class == MaterialsTableView


def test_materials_indicators_url_resolve():
    url = reverse("materials-indicators")
    resolver = resolve(url)

    assert resolver.func.view_class == MaterialsIndicatorsView


def test_materials_table_periodo_url_resolve():
    url = reverse("materials-table-periodo", kwargs={"periodo": "2024-03"})
    resolver = resolve(url)

    assert resolver.func.view_class == MaterialsTablePeriodoView
