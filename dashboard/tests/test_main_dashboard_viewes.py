# dashboard/tests/test_main_dashboard_views.py
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient

COMPOSITION_MOCK = {
    "custo_materiais": 450000.0,
    "custo_horas": 300000.0,
    "custo_total": 750000.0,
    "pct_materiais": 60.0,
    "pct_horas": 40.0,
}


# ── Existing test ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_projects_by_period")
def test_main_dashboard_endpoint_filters_by_period(mock_selector):
    client = APIClient()

    mock_selector.return_value = []

    response = client.get(
        "/api/dashboard/projects/?start_date=2026-01-01&end_date=2026-12-31"
    )

    assert response.status_code == 200
    assert response.data == []


# ── CT01: table display ───────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_returns_200_with_correct_fields(mock_selector):
    client = APIClient()
    mock_selector.return_value = [
        {
            "programa": "Programa A",
            "qtd_projetos": 3,
            "custo_materiais": 10000.0,
            "custo_horas": 5000.0,
            "custo_total": 15000.0,
        }
    ]

    response = client.get("/api/dashboard/summary/")

    assert response.status_code == 200
    assert len(response.data) == 1
    row = response.data[0]
    assert row["programa"] == "Programa A"
    assert row["qtd_projetos"] == 3
    assert row["custo_materiais"] == 10000.0
    assert row["custo_horas"] == 5000.0
    assert row["custo_total"] == 15000.0


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_returns_empty_list_when_no_data(mock_selector):
    client = APIClient()
    mock_selector.return_value = []

    response = client.get("/api/dashboard/summary/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_returns_multiple_programs(mock_selector):
    client = APIClient()
    mock_selector.return_value = [
        {
            "programa": "Programa A",
            "qtd_projetos": 2,
            "custo_materiais": 8000.0,
            "custo_horas": 2000.0,
            "custo_total": 10000.0,
        },
        {
            "programa": "Programa B",
            "qtd_projetos": 1,
            "custo_materiais": 3000.0,
            "custo_horas": 1000.0,
            "custo_total": 4000.0,
        },
    ]

    response = client.get("/api/dashboard/summary/")

    assert response.status_code == 200
    assert len(response.data) == 2


# ── CT02: filter response ─────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_passes_all_filters_to_selector(mock_selector):
    client = APIClient()
    mock_selector.return_value = []

    client.get(
        "/api/dashboard/summary/"
        "?start_date=2026-01-01&end_date=2026-12-31"
        "&programa=Programa+A&projeto=Projeto+X"
    )

    mock_selector.assert_called_once()
    params = mock_selector.call_args[0][0]
    assert params["start_date"] == "2026-01-01"
    assert params["end_date"] == "2026-12-31"
    assert params["programa"] == "Programa A"
    assert params["projeto"] == "Projeto X"


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_with_no_filters_calls_selector_with_empty_params(mock_selector):
    client = APIClient()
    mock_selector.return_value = []

    client.get("/api/dashboard/summary/")

    mock_selector.assert_called_once()
    params = mock_selector.call_args[0][0]
    assert params.get("start_date") is None
    assert params.get("programa") is None


# ── CT03: sorting (default server-side order preserved in response) ───────────


@pytest.mark.django_db
@patch("dashboard.views.get_program_summary")
def test_summary_table_preserves_selector_order(mock_selector):
    client = APIClient()
    mock_selector.return_value = [
        {
            "programa": "Maior Custo",
            "qtd_projetos": 1,
            "custo_materiais": 9000.0,
            "custo_horas": 1000.0,
            "custo_total": 10000.0,
        },
        {
            "programa": "Menor Custo",
            "qtd_projetos": 1,
            "custo_materiais": 1000.0,
            "custo_horas": 500.0,
            "custo_total": 1500.0,
        },
    ]

    response = client.get("/api/dashboard/summary/")

    assert response.data[0]["programa"] == "Maior Custo"
    assert response.data[1]["programa"] == "Menor Custo"


# ── CostCompositionView ───────────────────────────────────────────────────────

# ── CT01: percentage composition ─────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_returns_percentage_fields(mock_selector):
    client = APIClient()
    mock_selector.return_value = COMPOSITION_MOCK

    response = client.get("/api/dashboard/composition/")

    assert response.status_code == 200
    assert response.data["pct_materiais"] == 60.0
    assert response.data["pct_horas"] == 40.0


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_percentages_are_present_in_response(mock_selector):
    client = APIClient()
    mock_selector.return_value = {
        "custo_materiais": 250.0,
        "custo_horas": 750.0,
        "custo_total": 1000.0,
        "pct_materiais": 25.0,
        "pct_horas": 75.0,
    }

    response = client.get("/api/dashboard/composition/")

    assert "pct_materiais" in response.data
    assert "pct_horas" in response.data
    assert response.data["pct_materiais"] == 25.0
    assert response.data["pct_horas"] == 75.0


# ── CT02: absolute values ─────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_returns_absolute_cost_fields(mock_selector):
    client = APIClient()
    mock_selector.return_value = COMPOSITION_MOCK

    response = client.get("/api/dashboard/composition/")

    assert response.data["custo_materiais"] == 450000.0
    assert response.data["custo_horas"] == 300000.0
    assert response.data["custo_total"] == 750000.0


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_returns_all_five_fields(mock_selector):
    client = APIClient()
    mock_selector.return_value = COMPOSITION_MOCK

    response = client.get("/api/dashboard/composition/")

    for field in (
        "custo_materiais",
        "custo_horas",
        "custo_total",
        "pct_materiais",
        "pct_horas",
    ):
        assert field in response.data


# ── CT03: filter passing ──────────────────────────────────────────────────────


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_passes_filters_to_selector(mock_selector):
    client = APIClient()
    mock_selector.return_value = COMPOSITION_MOCK

    client.get(
        "/api/dashboard/composition/"
        "?start_date=2026-01-01&end_date=2026-06-30"
        "&programa=Programa+X&projeto=Projeto+Y"
    )

    mock_selector.assert_called_once()
    params = mock_selector.call_args[0][0]
    assert params["start_date"] == "2026-01-01"
    assert params["end_date"] == "2026-06-30"
    assert params["programa"] == "Programa X"
    assert params["projeto"] == "Projeto Y"


@pytest.mark.django_db
@patch("dashboard.views.get_cost_composition")
def test_composition_with_no_filters_still_returns_200(mock_selector):
    client = APIClient()
    mock_selector.return_value = {
        "custo_materiais": 0.0,
        "custo_horas": 0.0,
        "custo_total": 0.0,
        "pct_materiais": 0.0,
        "pct_horas": 0.0,
    }

    response = client.get("/api/dashboard/composition/")

    assert response.status_code == 200
    assert response.data["pct_materiais"] == 0.0
    assert response.data["pct_horas"] == 0.0
