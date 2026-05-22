# dashboard/tests/test_cost_evolution.py
import pytest
from unittest.mock import MagicMock, patch


from dashboard.selectors import get_cost_evolution
from dashboard.serializers import CostEvolutionSerializer


# ── Helpers ───────────────────────────────────────────────────────────────────

EVOLUTION_MOCK = [
    {
        "period": "2024-01",
        "materials_cost": 980000.0,
        "hours_cost": 450000.0,
        "total_cost": 1430000.0,
    },
    {
        "period": "2024-02",
        "materials_cost": 750000.0,
        "hours_cost": 380000.0,
        "total_cost": 1130000.0,
    },
    {
        "period": "2024-03",
        "materials_cost": 620000.0,
        "hours_cost": 310000.0,
        "total_cost": 930000.0,
    },
]


def _mock_cursor(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    return cursor


def _patch_cursor(cursor):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = cursor
    return patch("dashboard.selectors.connection", mock_conn)


# ── get_cost_evolution ────────────────────────────────────────────────────────


def test_get_cost_evolution_returns_list():
    rows = [("2024-01", 500.0, 200.0, 700.0), ("2024-02", 300.0, 150.0, 450.0)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    assert isinstance(result, list)
    assert len(result) == 2


def test_get_cost_evolution_returns_correct_fields():
    rows = [("2024-01", 980000.0, 450000.0, 1430000.0)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    assert result[0]["period"] == "2024-01"
    assert result[0]["materials_cost"] == pytest.approx(980000.0)
    assert result[0]["hours_cost"] == pytest.approx(450000.0)
    assert result[0]["total_cost"] == pytest.approx(1430000.0)


def test_get_cost_evolution_rounds_to_two_decimals():
    rows = [("2024-01", 100000.555, 50000.444, 150000.999)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    assert result[0]["materials_cost"] == pytest.approx(round(100000.555, 2))
    assert result[0]["hours_cost"] == pytest.approx(round(50000.444, 2))
    assert result[0]["total_cost"] == pytest.approx(round(150000.999, 2))


# CT01: validate aggregation by period
def test_ct01_aggregation_by_period_returns_sorted_months():
    rows = [
        ("2024-01", 500.0, 200.0, 700.0),
        ("2024-02", 300.0, 150.0, 450.0),
        ("2024-03", 400.0, 180.0, 580.0),
    ]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    periods = [r["period"] for r in result]
    assert periods == sorted(periods)


def test_ct01_each_period_has_all_cost_fields():
    rows = [("2024-01", 1000.0, 500.0, 1500.0)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    row = result[0]
    assert "period" in row
    assert "materials_cost" in row
    assert "hours_cost" in row
    assert "total_cost" in row


def test_ct01_total_cost_equals_sum_of_parts():
    rows = [("2024-01", 300000.0, 150000.0, 450000.0)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    r = result[0]
    assert r["total_cost"] == r["materials_cost"] + r["hours_cost"]


def test_ct01_sql_uses_union_all():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({})

    sql, _ = cursor.execute.call_args[0]
    assert "UNION ALL" in sql
    assert "TO_CHAR" in sql
    assert "periodo" in sql.lower() or "YYYY-MM" in sql


def test_ct01_sql_orders_by_period_ascending():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({})

    sql, _ = cursor.execute.call_args[0]
    assert "ORDER BY periodo ASC" in sql


# CT02: validate response to filters
def test_ct02_start_date_filter_included_in_sql():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({"start_date": "2024-01-01"})

    sql, values = cursor.execute.call_args[0]
    assert "data_pedido >= %(start_date)s" in sql
    assert "tt.data >= %(start_date)s" in sql
    assert values["start_date"] == "2024-01-01"


def test_ct02_end_date_filter_included_in_sql():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({"end_date": "2024-12-31"})

    sql, values = cursor.execute.call_args[0]
    assert "data_pedido <= %(end_date)s" in sql
    assert "tt.data <= %(end_date)s" in sql
    assert values["end_date"] == "2024-12-31"


def test_ct02_program_filter_applied_to_both_subqueries():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({"program": "MANSUP"})

    sql, values = cursor.execute.call_args[0]
    assert sql.count("prog.nome_programa ILIKE %(program)s") == 2
    assert values["program"] == "MANSUP"


def test_ct02_project_filter_applied_to_both_subqueries():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({"project": "Conversor DC"})

    sql, values = cursor.execute.call_args[0]
    assert sql.count("p.nome_projeto ILIKE %(project)s") == 2
    assert values["project"] == "Conversor DC"


def test_ct02_status_filter_applied_to_both_subqueries():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({"status": "Em andamento"})

    sql, values = cursor.execute.call_args[0]
    assert sql.count("p.status ILIKE %(status)s") == 2
    assert values["status"] == "Em andamento"


def test_ct02_no_filters_passes_empty_values():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({})

    _, values = cursor.execute.call_args[0]
    assert values == {}


def test_ct02_all_filters_combined():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution(
            {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "program": "MANSUP",
                "project": "Conversor DC",
                "status": "Em andamento",
            }
        )

    _, values = cursor.execute.call_args[0]
    assert len(values) == 5


# CT03: validate behavior during periods with no data
def test_ct03_empty_result_returns_empty_list():
    with _patch_cursor(_mock_cursor([])):
        result = get_cost_evolution({})

    assert result == []


def test_ct03_zero_cost_period_is_included():
    rows = [("2024-01", 1000.0, 500.0, 1500.0), ("2024-02", 0.0, 0.0, 0.0)]
    with _patch_cursor(_mock_cursor(rows)):
        result = get_cost_evolution({})

    assert len(result) == 2
    assert result[1]["total_cost"] == pytest.approx(0.0)


def test_ct03_sql_uses_coalesce_for_null_safety():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({})

    sql, _ = cursor.execute.call_args[0]
    assert "COALESCE" in sql


def test_ct03_executes_single_query():
    cursor = _mock_cursor([])
    with _patch_cursor(cursor):
        get_cost_evolution({})

    assert cursor.execute.call_count == 1


# ── CostEvolutionSerializer ───────────────────────────────────────────────────


def test_serializer_contains_all_fields():
    data = {
        "period": "2024-01",
        "materials_cost": 980000.0,
        "hours_cost": 450000.0,
        "total_cost": 1430000.0,
    }
    s = CostEvolutionSerializer(data)
    assert set(s.data.keys()) == {
        "period",
        "materials_cost",
        "hours_cost",
        "total_cost",
    }


def test_serializer_correct_values():
    data = {
        "period": "2024-03",
        "materials_cost": 300.0,
        "hours_cost": 150.0,
        "total_cost": 450.0,
    }
    s = CostEvolutionSerializer(data)
    assert s.data["period"] == "2024-03"
    assert s.data["total_cost"] == pytest.approx(450.0)


def test_serializer_many_true():
    s = CostEvolutionSerializer(EVOLUTION_MOCK, many=True)
    assert len(s.data) == 3


def test_serializer_cost_fields_are_float():
    data = {
        "period": "2024-01",
        "materials_cost": 1000.0,
        "hours_cost": 500.0,
        "total_cost": 1500.0,
    }
    s = CostEvolutionSerializer(data)
    assert isinstance(s.data["materials_cost"], float)
    assert isinstance(s.data["hours_cost"], float)
    assert isinstance(s.data["total_cost"], float)


def test_serializer_period_is_string():
    data = {
        "period": "2024-01",
        "materials_cost": 0.0,
        "hours_cost": 0.0,
        "total_cost": 0.0,
    }
    s = CostEvolutionSerializer(data)
    assert isinstance(s.data["period"], str)


# ── GET /api/dashboard/cost-evolution/ ───────────────────────────────────────


@pytest.mark.django_db
def test_endpoint_returns_200(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=EVOLUTION_MOCK):
        response = api_client.get("/api/dashboard/cost-evolution/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_endpoint_returns_list(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=EVOLUTION_MOCK):
        response = api_client.get("/api/dashboard/cost-evolution/")
    assert isinstance(response.data, list)
    assert len(response.data) == 3


@pytest.mark.django_db
def test_endpoint_response_fields(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=EVOLUTION_MOCK):
        response = api_client.get("/api/dashboard/cost-evolution/")
    row = response.data[0]
    assert "period" in row
    assert "materials_cost" in row
    assert "hours_cost" in row
    assert "total_cost" in row


@pytest.mark.django_db
def test_endpoint_passes_all_filters_to_selector(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=[]) as mock_sel:
        api_client.get(
            "/api/dashboard/cost-evolution/"
            "?start_date=2024-01-01&end_date=2024-12-31"
            "&program=MANSUP&project=Conversor&status=Em+andamento"
        )
    called = mock_sel.call_args[0][0]
    assert called["start_date"] == "2024-01-01"
    assert called["end_date"] == "2024-12-31"
    assert called["program"] == "MANSUP"
    assert called["project"] == "Conversor"
    assert called["status"] == "Em andamento"


@pytest.mark.django_db
def test_endpoint_no_filters_returns_all(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=EVOLUTION_MOCK):
        response = api_client.get("/api/dashboard/cost-evolution/")
    assert response.status_code == 200
    assert len(response.data) == 3


@pytest.mark.django_db
def test_endpoint_empty_returns_empty_list(api_client):
    with patch("dashboard.views.get_cost_evolution", return_value=[]):
        response = api_client.get("/api/dashboard/cost-evolution/")
    assert response.status_code == 200
    assert response.data == []


# ── URL ───────────────────────────────────────────────────────────────────────


def test_url_resolves():
    from django.urls import resolve, reverse
    from dashboard.views import CostEvolutionView

    assert (
        resolve(reverse("dashboard-cost-evolution")).func.view_class
        == CostEvolutionView
    )


def test_url_path():
    from django.urls import reverse

    assert reverse("dashboard-cost-evolution") == "/api/dashboard/cost-evolution/"
