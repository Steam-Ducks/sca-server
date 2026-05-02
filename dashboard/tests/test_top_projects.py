# dashboard/tests/test_top_projects.py
import pytest
from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient

from dashboard.selectors import get_top_projects_by_cost
from dashboard.serializers import TopProjectSerializer


# ── Helpers ───────────────────────────────────────────────────────────────────

TOP_MOCK = [
    {"project_name": "Projeto Alpha", "total_cost": 980000.00},
    {"project_name": "Projeto Beta", "total_cost": 750000.00},
    {"project_name": "Projeto Gamma", "total_cost": 530000.00},
]


def _mock_cursor(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    return cursor


def _patch_cursor(cursor):
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = cursor
    return patch("dashboard.selectors.connection", mock_conn)


# ── get_top_projects_by_cost ──────────────────────────────────────────────────


def test_get_top_projects_returns_list():
    rows = [("Projeto Alpha", 980000.0), ("Projeto Beta", 750000.0)]
    patcher = _patch_cursor(_mock_cursor(rows))

    with patcher:
        result = get_top_projects_by_cost({})

    assert isinstance(result, list)
    assert len(result) == 2


def test_get_top_projects_returns_correct_fields():
    rows = [("Projeto Alpha", 980000.0)]
    patcher = _patch_cursor(_mock_cursor(rows))

    with patcher:
        result = get_top_projects_by_cost({})

    assert "project_name" in result[0]
    assert "total_cost" in result[0]


def test_get_top_projects_correct_values():
    rows = [("Projeto Alpha", 980000.0), ("Projeto Beta", 750000.55)]
    patcher = _patch_cursor(_mock_cursor(rows))

    with patcher:
        result = get_top_projects_by_cost({})

    assert result[0]["project_name"] == "Projeto Alpha"
    assert result[0]["total_cost"] == 980000.0
    assert result[1]["total_cost"] == 750000.55


def test_get_top_projects_rounds_to_two_decimals():
    rows = [("Projeto X", 123456.789)]
    patcher = _patch_cursor(_mock_cursor(rows))

    with patcher:
        result = get_top_projects_by_cost({})

    assert result[0]["total_cost"] == round(123456.789, 2)


def test_get_top_projects_empty_result():
    patcher = _patch_cursor(_mock_cursor([]))

    with patcher:
        result = get_top_projects_by_cost({})

    assert result == []


def test_get_top_projects_executes_one_query():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({})

    assert cursor.execute.call_count == 1


def test_get_top_projects_no_filters_passes_empty_values():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({})

    _, call_values = cursor.execute.call_args[0]
    assert call_values == {}


def test_get_top_projects_with_start_date_passes_value():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({"start_date": "2024-01-01"})

    _, call_values = cursor.execute.call_args[0]
    assert call_values["start_date"] == "2024-01-01"


def test_get_top_projects_with_end_date_passes_value():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({"end_date": "2024-12-31"})

    _, call_values = cursor.execute.call_args[0]
    assert call_values["end_date"] == "2024-12-31"


def test_get_top_projects_with_program_filter():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({"program": "MANSUP"})

    sql, call_values = cursor.execute.call_args[0]
    assert call_values["program"] == "MANSUP"
    assert "prog.nome_programa ILIKE %(program)s" in sql


def test_get_top_projects_with_project_filter():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({"project": "Conversor DC"})

    sql, call_values = cursor.execute.call_args[0]
    assert call_values["project"] == "Conversor DC"
    assert "p.nome_projeto ILIKE %(project)s" in sql


def test_get_top_projects_with_status_filter():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({"status": "Em andamento"})

    sql, call_values = cursor.execute.call_args[0]
    assert call_values["status"] == "Em andamento"
    assert "p.status ILIKE %(status)s" in sql


def test_get_top_projects_sql_contains_limit_10():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({})

    sql, _ = cursor.execute.call_args[0]
    assert "LIMIT 10" in sql


def test_get_top_projects_sql_contains_order_by_desc():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({})

    sql, _ = cursor.execute.call_args[0]
    assert "ORDER BY total_cost DESC" in sql


def test_get_top_projects_sql_uses_subqueries():
    cursor = _mock_cursor([])
    patcher = _patch_cursor(cursor)

    with patcher:
        get_top_projects_by_cost({})

    sql, _ = cursor.execute.call_args[0]
    assert "silver.compras_projeto" in sql
    assert "silver.tempo_tarefas" in sql
    assert "valor_alocado" in sql
    assert "horas_trabalhadas" in sql


# ── TopProjectSerializer ──────────────────────────────────────────────────────


def test_top_project_serializer_contains_all_fields():
    data = {"project_name": "Projeto Alpha", "total_cost": 980000.0}
    s = TopProjectSerializer(data)
    assert "project_name" in s.data
    assert "total_cost" in s.data


def test_top_project_serializer_correct_values():
    data = {"project_name": "Projeto Beta", "total_cost": 750000.0}
    s = TopProjectSerializer(data)
    assert s.data["project_name"] == "Projeto Beta"
    assert s.data["total_cost"] == 750000.0


def test_top_project_serializer_many_true():
    items = [
        {"project_name": "Alpha", "total_cost": 100.0},
        {"project_name": "Beta", "total_cost": 50.0},
    ]
    s = TopProjectSerializer(items, many=True)
    assert len(s.data) == 2


def test_top_project_serializer_total_cost_is_float():
    data = {"project_name": "X", "total_cost": 123456.78}
    s = TopProjectSerializer(data)
    assert isinstance(s.data["total_cost"], float)


# ── GET /api/dashboard/top-projects/ ─────────────────────────────────────────


@pytest.mark.django_db
def test_top_projects_endpoint_returns_200():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=TOP_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/top-projects/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_top_projects_endpoint_returns_list():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=TOP_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/top-projects/")

    assert isinstance(response.data, list)
    assert len(response.data) == 3


@pytest.mark.django_db
def test_top_projects_endpoint_response_fields():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=TOP_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/top-projects/")

    row = response.data[0]
    assert "project_name" in row
    assert "total_cost" in row


@pytest.mark.django_db
def test_top_projects_endpoint_passes_filters_to_selector():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=[]) as mock_sel:
        client = APIClient()
        client.get(
            "/api/dashboard/top-projects/"
            "?start_date=2024-01-01&end_date=2024-12-31"
            "&program=MANSUP&project=Conversor&status=Em+andamento"
        )

    called_with = mock_sel.call_args[0][0]
    assert called_with["start_date"] == "2024-01-01"
    assert called_with["end_date"] == "2024-12-31"
    assert called_with["program"] == "MANSUP"
    assert called_with["project"] == "Conversor"
    assert called_with["status"] == "Em andamento"


@pytest.mark.django_db
def test_top_projects_endpoint_no_filters_calls_selector_with_empty_params():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=[]) as mock_sel:
        client = APIClient()
        client.get("/api/dashboard/top-projects/")

    called_with = mock_sel.call_args[0][0]
    assert called_with.get("program") is None
    assert called_with.get("project") is None
    assert called_with.get("status") is None


@pytest.mark.django_db
def test_top_projects_endpoint_returns_empty_list_when_no_data():
    with patch("dashboard.views.get_top_projects_by_cost", return_value=[]):
        client = APIClient()
        response = client.get("/api/dashboard/top-projects/")

    assert response.status_code == 200
    assert response.data == []


# ── URL ───────────────────────────────────────────────────────────────────────


def test_top_projects_url_resolves():
    from django.urls import resolve, reverse
    from dashboard.views import TopProjectsView

    url = reverse("dashboard-top-projects")
    resolver = resolve(url)
    assert resolver.func.view_class == TopProjectsView


def test_top_projects_url_path():
    from django.urls import reverse

    url = reverse("dashboard-top-projects")
    assert url == "/api/dashboard/top-projects/"
