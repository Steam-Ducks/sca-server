from rest_framework.test import APIClient
import pytest


@pytest.fixture
def client():
    return APIClient()


# HEALTH CHECK
def test_health_check_returns_200_and_status_ok(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.data == {"status": "ok"}


# DASHBOARD
# Verifies that the dashboard endpoint returns the expected response structure
@pytest.mark.django_db
def test_dashboard_returns_expected_structure(client):
    response = client.get("/api/dashboard/")

    assert response.status_code == 200

    assert set(response.data.keys()) == {
        "users",
        "orders",
        "alerts",
        "start_date",
        "end_date",
    }


# Ensures that dashboard metrics are returned as numeric values
@pytest.mark.django_db
def test_dashboard_returns_numeric_values(client):
    response = client.get("/api/dashboard/")

    assert isinstance(response.data["users"], int)
    assert isinstance(response.data["orders"], int)
    assert isinstance(response.data["alerts"], int)


# Validates that the API correctly applies the date range filter
@pytest.mark.django_db
def test_dashboard_applies_date_filter_correctly(client):
    response = client.get(
        "/api/dashboard/?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == 200
    assert response.data["start_date"] == "2026-01-01"
    assert response.data["end_date"] == "2026-01-31"


# Ensures that when no filter is provided, the API returns null values for dates
@pytest.mark.django_db
def test_dashboard_without_filters_returns_null_dates(client):
    response = client.get("/api/dashboard/")

    assert response.status_code == 200
    assert response.data["start_date"] is None
    assert response.data["end_date"] is None


# Confirms that applying a filter changes the response compared to no filter
@pytest.mark.django_db
def test_dashboard_filter_changes_response(client):
    response_with_filter = client.get(
        "/api/dashboard/?start_date=2026-01-01&end_date=2026-01-31"
    )

    response_without_filter = client.get("/api/dashboard/")

    assert response_with_filter.status_code == 200
    assert response_without_filter.status_code == 200
    assert response_with_filter.data != response_without_filter.data


# Ensures that the dashboard endpoint is available and responding.
@pytest.mark.django_db
def test_dashboard_endpoint_is_available(client):
    response = client.get("/api/dashboard/")

    assert response.status_code == 200