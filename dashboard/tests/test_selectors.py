# dashboard/tests/test_selectors.py
from unittest.mock import MagicMock, patch

from dashboard.selectors import (
    build_filters,
    get_cost_composition,
    get_dashboard_kpis,
    get_program_summary,
    get_projects_by_period,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_cursor(
    materials_cost=450000.0,
    hours_cost=300000.0,
    total_projects=8,
    total_programs=3,
):
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        (materials_cost,),
        (hours_cost,),
        (total_projects,),
        (total_programs,),
    ]
    return cursor


def _patch_cursor(cursor):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = cursor
    return patch("dashboard.selectors.connection", mock_conn), mock_conn


# ── build_filters ─────────────────────────────────────────────────────────────


def test_build_filters_no_params_returns_empty_clauses():
    mat, hrs, prj, values = build_filters({})

    assert mat == ""
    assert hrs == ""
    assert prj == ""
    assert values == {}


def test_build_filters_start_date():
    mat, hrs, prj, values = build_filters({"start_date": "2024-01-01"})

    assert "pc.data_pedido >= %(start_date)s" in mat
    assert "tt.data >= %(start_date)s" in hrs
    assert prj == ""
    assert values["start_date"] == "2024-01-01"


def test_build_filters_end_date():
    mat, hrs, prj, values = build_filters({"end_date": "2024-12-31"})

    assert "pc.data_pedido <= %(end_date)s" in mat
    assert "tt.data <= %(end_date)s" in hrs
    assert values["end_date"] == "2024-12-31"


def test_build_filters_program():
    mat, hrs, prj, values = build_filters({"program": "MANSUP"})

    assert "prog.codigo_programa = %(program)s" in mat
    assert "prog.codigo_programa = %(program)s" in hrs
    assert "prog.codigo_programa = %(program)s" in prj
    assert values["program"] == "MANSUP"


def test_build_filters_project():
    mat, hrs, prj, values = build_filters({"project": "Sensor Pressão Industrial"})

    assert "p.nome_projeto = %(project)s" in mat
    assert "p.nome_projeto = %(project)s" in hrs
    assert "p.nome_projeto = %(project)s" in prj
    assert values["project"] == "Sensor Pressão Industrial"


def test_build_filters_status():
    mat, hrs, prj, values = build_filters({"status": "Em andamento"})

    assert "p.status = %(status)s" in mat
    assert "p.status = %(status)s" in hrs
    assert "p.status = %(status)s" in prj
    assert values["status"] == "Em andamento"


def test_build_filters_all_params():
    params = {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "program": "MANSUP",
        "project": "Sensor Pressão Industrial",
        "status": "Concluído",
    }
    mat, hrs, prj, values = build_filters(params)

    assert mat.startswith("WHERE ")
    assert hrs.startswith("WHERE ")
    assert prj.startswith("WHERE ")
    assert len(values) == 5


def test_build_filters_clauses_start_with_where_when_filtered():
    mat, hrs, prj, values = build_filters({"project": "Sensor Pressão Industrial"})

    assert mat.startswith("WHERE ")
    assert hrs.startswith("WHERE ")
    assert prj.startswith("WHERE ")


# ── get_dashboard_kpis ────────────────────────────────────────────────────────


def test_get_dashboard_kpis_returns_five_fields():
    cursor = _mock_cursor()
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        result = get_dashboard_kpis({})

    assert "total_consolidated_cost" in result
    assert "total_materials_cost" in result
    assert "total_hours_cost" in result
    assert "total_projects" in result
    assert "total_programs" in result


def test_get_dashboard_kpis_correct_values():
    cursor = _mock_cursor(
        materials_cost=450000.0,
        hours_cost=300000.0,
        total_projects=8,
        total_programs=3,
    )
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        result = get_dashboard_kpis({})

    assert result["total_materials_cost"] == 450000.0
    assert result["total_hours_cost"] == 300000.0
    assert result["total_projects"] == 8
    assert result["total_programs"] == 3


def test_get_dashboard_kpis_consolidated_is_sum_of_materials_and_hours():
    cursor = _mock_cursor(materials_cost=450000.0, hours_cost=300000.0)
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        result = get_dashboard_kpis({})

    assert result["total_consolidated_cost"] == 750000.0


def test_get_dashboard_kpis_rounds_to_two_decimals():
    cursor = _mock_cursor(materials_cost=100000.555, hours_cost=200000.444)
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        result = get_dashboard_kpis({})

    assert result["total_materials_cost"] == round(100000.555, 2)
    assert result["total_hours_cost"] == round(200000.444, 2)
    assert result["total_consolidated_cost"] == round(100000.555 + 200000.444, 2)


def test_get_dashboard_kpis_executes_four_queries():
    cursor = _mock_cursor()
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        get_dashboard_kpis({})

    assert cursor.execute.call_count == 4


def test_get_dashboard_kpis_no_filters_passes_empty_values():
    cursor = _mock_cursor()
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        get_dashboard_kpis({})

    for call in cursor.execute.call_args_list:
        _, values = call[0]
        assert values == {}


def test_get_dashboard_kpis_passes_filters_to_queries():
    cursor = _mock_cursor()
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        get_dashboard_kpis({"program": "MANSUP", "status": "Em andamento"})

    for call in cursor.execute.call_args_list:
        _, values = call[0]
        assert values["program"] == "MANSUP"
        assert values["status"] == "Em andamento"


def test_get_dashboard_kpis_with_zeros():
    cursor = _mock_cursor(
        materials_cost=0.0,
        hours_cost=0.0,
        total_projects=0,
        total_programs=0,
    )
    patcher, _ = _patch_cursor(cursor)

    with patcher:
        result = get_dashboard_kpis({})

    assert result["total_consolidated_cost"] == 0.0
    assert result["total_materials_cost"] == 0.0
    assert result["total_hours_cost"] == 0.0
    assert result["total_projects"] == 0
    assert result["total_programs"] == 0


# ── get_projects_by_period ────────────────────────────────────────────────────

@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_no_dates_calls_filter_with_empty_q(mock_objects):
    mock_objects.filter.return_value = []

    get_projects_by_period()

    mock_objects.filter.assert_called_once()


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_with_start_date(mock_objects):
    mock_objects.filter.return_value = []

    get_projects_by_period(start_date="2024-01-01")

    call_args = mock_objects.filter.call_args[0][0]
    assert "silver_ingested_at__date__gte" in str(call_args)


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_with_end_date(mock_objects):
    mock_objects.filter.return_value = []

    get_projects_by_period(end_date="2024-12-31")

    call_args = mock_objects.filter.call_args[0][0]
    assert "silver_ingested_at__date__lte" in str(call_args)


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_with_both_dates(mock_objects):
    mock_objects.filter.return_value = []

    get_projects_by_period(start_date="2024-01-01", end_date="2024-12-31")

    call_args = mock_objects.filter.call_args[0][0]
    assert "silver_ingested_at__date__gte" in str(call_args)
    assert "silver_ingested_at__date__lte" in str(call_args)


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_returns_queryset(mock_objects):
    mock_qs = MagicMock()
    mock_objects.filter.return_value = mock_qs

    result = get_projects_by_period()

    assert result == mock_qs


# ── _build_cost_filters — date branches ──────────────────────────────────────

@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_with_start_date_applies_compras_filter(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({"start_date": "2024-01-01"})

    annotate_call = mock_qs.annotate.call_args
    assert annotate_call is not None


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_with_end_date_applies_tempo_filter(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({"end_date": "2024-12-31"})

    annotate_call = mock_qs.annotate.call_args
    assert annotate_call is not None


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_program_summary_with_both_dates(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    mock_qs.order_by.return_value = []

    get_program_summary({"start_date": "2024-01-01", "end_date": "2024-12-31"})

    mock_qs.annotate.assert_called_once()


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_with_start_date(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.aggregate.return_value = {"custo_materiais": 0.0, "custo_horas": 0.0}

    result = get_cost_composition({"start_date": "2024-01-01"})

    mock_qs.aggregate.assert_called_once()
    assert result["pct_materiais"] == 0.0


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_with_end_date(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.aggregate.return_value = {"custo_materiais": 500.0, "custo_horas": 500.0}

    result = get_cost_composition({"end_date": "2024-12-31"})

    assert result["custo_total"] == 1000.0
    assert result["pct_materiais"] == 50.0
    assert result["pct_horas"] == 50.0


@patch("dashboard.selectors.SilverProjeto.objects")
def test_get_cost_composition_with_both_dates(mock_objects):
    mock_qs = MagicMock()
    mock_objects.select_related.return_value = mock_qs
    mock_qs.aggregate.return_value = {"custo_materiais": 300.0, "custo_horas": 700.0}

    result = get_cost_composition({"start_date": "2024-01-01", "end_date": "2024-12-31"})

    assert result["custo_total"] == 1000.0
    assert result["pct_materiais"] == 30.0
    assert result["pct_horas"] == 70.0