import pytest
from unittest.mock import patch
from rest_framework.test import APIClient


@pytest.mark.django_db
@patch("main_dashboard.views.get_projects_by_period")
def test_main_dashboard_endpoint_filters_by_period(mock_selector):
    client = APIClient()

    mock_selector.return_value = []

    response = client.get(
        "/api/main-dashboard/?start_date=2026-01-01&end_date=2026-12-31"
    )

    assert response.status_code == 200
    assert response.data == []
