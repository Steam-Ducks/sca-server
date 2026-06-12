"""Garante que as views de listagem filtrada foram migradas para a base comum
``BaseFilteredListView`` sem alterar o prefixo de cache de cada endpoint."""

from core.views import BaseFilteredListView
from costs.views import GoldCostsTableView
from materials.views import MaterialsTablePeriodoView, MaterialsTableView
from technical_hours.views import (
    TechnicalHoursTablePeriodoView,
    TechnicalHoursTableView,
)


def test_costs_table_view_migrated():
    assert issubclass(GoldCostsTableView, BaseFilteredListView)
    assert GoldCostsTableView.cache_key_prefix == "gold_costs"


def test_materials_table_view_migrated():
    assert issubclass(MaterialsTableView, BaseFilteredListView)
    assert MaterialsTableView.cache_key_prefix == "materials_table"


def test_materials_periodo_view_migrated():
    assert issubclass(MaterialsTablePeriodoView, BaseFilteredListView)
    assert MaterialsTablePeriodoView.cache_key_prefix == "materials_table_p"


def test_materials_periodo_cache_key_includes_periodo():
    view = MaterialsTablePeriodoView()
    view.kwargs = {"periodo": "2024-03"}
    assert view.get_cache_key_extra() == {"periodo": "2024-03"}


def test_technical_hours_table_view_migrated():
    assert issubclass(TechnicalHoursTableView, BaseFilteredListView)
    assert TechnicalHoursTableView.cache_key_prefix == "tech_hours_table"


def test_technical_hours_periodo_view_migrated():
    assert issubclass(TechnicalHoursTablePeriodoView, BaseFilteredListView)
    assert TechnicalHoursTablePeriodoView.cache_key_prefix == "tech_hours_table_p"


def test_technical_hours_periodo_cache_key_includes_periodo():
    view = TechnicalHoursTablePeriodoView()
    view.kwargs = {"periodo": "2024-03"}
    assert view.get_cache_key_extra() == {"periodo": "2024-03"}
