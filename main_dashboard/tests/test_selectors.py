import pytest
from unittest.mock import MagicMock, patch

from main_dashboard.selectors import (
    get_cost_composition,
    get_program_summary,
    get_projects_by_period,
)


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_filters_correctly(mock_objects):
    mock_qs = mock_objects.filter.return_value

    result = get_projects_by_period("2026-01-01", "2026-12-31")

    mock_objects.filter.assert_called()
    assert result == mock_qs


# ── CT01: table display ───────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_returns_expected_shape(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = [
        {
            "programa__nome_programa": "Programa A",
            "qtd_projetos": 2,
            "custo_materiais": 1000.0,
            "custo_horas": 500.0,
        }
    ]

    result = get_program_summary({})

    assert len(result) == 1
    row = result[0]
    assert row["programa"] == "Programa A"
    assert row["qtd_projetos"] == 2
    assert row["custo_materiais"] == 1000.0
    assert row["custo_horas"] == 500.0
    assert row["custo_total"] == 1500.0


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_custo_total_is_sum_of_parts(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = [
        {
            "programa__nome_programa": "X",
            "qtd_projetos": 1,
            "custo_materiais": 3333.33,
            "custo_horas": 1666.67,
        }
    ]

    result = get_program_summary({})

    assert result[0]["custo_total"] == round(3333.33 + 1666.67, 2)


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_null_program_becomes_sem_programa(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = [
        {
            "programa__nome_programa": None,
            "qtd_projetos": 1,
            "custo_materiais": 0.0,
            "custo_horas": 0.0,
        }
    ]

    result = get_program_summary({})

    assert result[0]["programa"] == "Sem Programa"


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_empty_dataset(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    result = get_program_summary({})

    assert result == []


# ── CT02: filter response ─────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_applies_programa_filter(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({"programa": "Programa A"})

    mock_qs.filter.assert_any_call(programa__nome_programa__iexact="Programa A")


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_applies_projeto_filter(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({"projeto": "Projeto X"})

    mock_qs.filter.assert_any_call(nome_projeto__iexact="Projeto X")


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_no_filter_skips_filter_call(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({})

    mock_qs.filter.assert_not_called()


# ── CT03: ordering ────────────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_orders_by_custo_materiais_desc(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({})

    mock_qs.order_by.assert_called_once_with("-custo_materiais")


# ── get_cost_composition ──────────────────────────────────────────────────────


def _composition_mock(mock_objects, custo_materiais=0.0, custo_horas=0.0):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.filter.return_value = mock_qs
    mock_qs.aggregate.return_value = {
        "custo_materiais": custo_materiais,
        "custo_horas": custo_horas,
    }
    return mock_qs


# ── CT01: percentage composition ─────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_calculates_percentages(mock_objects):
    _composition_mock(mock_objects, custo_materiais=600.0, custo_horas=400.0)

    result = get_cost_composition({})

    assert result["pct_materiais"] == 60.0
    assert result["pct_horas"] == 40.0


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_percentages_sum_to_100(mock_objects):
    _composition_mock(mock_objects, custo_materiais=750.0, custo_horas=250.0)

    result = get_cost_composition({})

    assert round(result["pct_materiais"] + result["pct_horas"], 1) == 100.0


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_zero_total_returns_zero_percentages(mock_objects):
    _composition_mock(mock_objects, custo_materiais=0.0, custo_horas=0.0)

    result = get_cost_composition({})

    assert result["pct_materiais"] == 0.0
    assert result["pct_horas"] == 0.0


# ── CT02: absolute values ─────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_returns_absolute_values(mock_objects):
    _composition_mock(mock_objects, custo_materiais=450000.0, custo_horas=300000.0)

    result = get_cost_composition({})

    assert result["custo_materiais"] == 450000.0
    assert result["custo_horas"] == 300000.0
    assert result["custo_total"] == 750000.0


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_rounds_to_two_decimals(mock_objects):
    _composition_mock(mock_objects, custo_materiais=333.333, custo_horas=166.667)

    result = get_cost_composition({})

    assert result["custo_materiais"] == 333.33
    assert result["custo_horas"] == 166.67
    assert result["custo_total"] == round(333.33 + 166.67, 2)


# ── CT03: filter application ──────────────────────────────────────────────────


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_applies_programa_filter(mock_objects):
    mock_qs = _composition_mock(mock_objects)

    get_cost_composition({"programa": "Programa X"})

    mock_qs.filter.assert_any_call(programa__nome_programa__iexact="Programa X")


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_applies_projeto_filter(mock_objects):
    mock_qs = _composition_mock(mock_objects)

    get_cost_composition({"projeto": "Projeto Y"})

    mock_qs.filter.assert_any_call(nome_projeto__iexact="Projeto Y")


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_no_filter_skips_filter_call(mock_objects):
    mock_qs = _composition_mock(mock_objects)

    get_cost_composition({})

    mock_qs.filter.assert_not_called()
