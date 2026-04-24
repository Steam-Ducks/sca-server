import pytest
from unittest.mock import patch
from main_dashboard.selectors import get_projects_by_period


@pytest.mark.django_db
@patch("main_dashboard.selectors.SilverProjeto.objects")
def test_get_projects_by_period_filters_correctly(mock_objects):
    mock_qs = mock_objects.filter.return_value

    result = get_projects_by_period("2026-01-01", "2026-12-31")

    mock_objects.filter.assert_called()
    assert result == mock_qs