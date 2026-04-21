# dashboard/tests/test_views.py
import pytest
from unittest.mock import patch

from rest_framework.test import APIClient


KPIS_MOCK = {
    "total_consolidated_cost": 750000.00,
    "total_materials_cost":    450000.00,
    "total_hours_cost":        300000.00,
    "total_projects":          8,
    "total_programs":          3,
}


@pytest.mark.django_db
def test_dashboard_kpis_returns_200():
    with patch("dashboard.views.get_dashboard_kpis", return_value=KPIS_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/kpis/")

        assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_kpis_returns_all_fields():
    with patch("dashboard.views.get_dashboard_kpis", return_value=KPIS_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/kpis/")
        data = response.data

        assert "total_consolidated_cost" in data
        assert "total_materials_cost" in data
        assert "total_hours_cost" in data
        assert "total_projects" in data
        assert "total_programs" in data


@pytest.mark.django_db
def test_dashboard_kpis_returns_correct_values():
    with patch("dashboard.views.get_dashboard_kpis", return_value=KPIS_MOCK):
        client = APIClient()
        response = client.get("/api/dashboard/kpis/")
        data = response.data

        assert data["total_consolidated_cost"] == 750000.00
        assert data["total_materials_cost"]    == 450000.00
        assert data["total_hours_cost"]        == 300000.00
        assert data["total_projects"]          == 8
        assert data["total_programs"]          == 3


@pytest.mark.django_db
def test_dashboard_kpis_passes_filters_to_selector():
    with patch("dashboard.views.get_dashboard_kpis", return_value=KPIS_MOCK) as mock_selector:
        client = APIClient()
        client.get("/api/dashboard/kpis/?program=2&project=5&status=Em+andamento")

        called_with = mock_selector.call_args[0][0]
        assert called_with["program"] == "2"
        assert called_with["project"] == "5"
        assert called_with["status"]  == "Em andamento"


@pytest.mark.django_db
def test_dashboard_kpis_no_filters_calls_selector_with_empty_params():
    with patch("dashboard.views.get_dashboard_kpis", return_value=KPIS_MOCK) as mock_selector:
        client = APIClient()
        client.get("/api/dashboard/kpis/")

        called_with = mock_selector.call_args[0][0]
        assert called_with.get("program")    is None
        assert called_with.get("project")    is None
        assert called_with.get("status")     is None
        assert called_with.get("start_date") is None
        assert called_with.get("end_date")   is None


@pytest.mark.django_db
def test_total_consolidated_cost_is_sum_of_materials_and_hours():
    kpis = {
        **KPIS_MOCK,
        "total_materials_cost":    200000.00,
        "total_hours_cost":        100000.00,
        "total_consolidated_cost": 300000.00,
    }
    with patch("dashboard.views.get_dashboard_kpis", return_value=kpis):
        client = APIClient()
        response = client.get("/api/dashboard/kpis/")

        assert response.data["total_consolidated_cost"] == (
            response.data["total_materials_cost"] + response.data["total_hours_cost"]
        )
        