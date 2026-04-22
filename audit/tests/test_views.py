import uuid
import datetime

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory

from audit.views import AuditExecutionLogTableView


def _make_log(status="SUCCESS", operation="INGEST", started_at=None, finalized_at=None):
    log = MagicMock()
    log.id = 1
    log.run_id = uuid.uuid4()
    log.operation = operation
    log.status = status
    log.table_schema = "bronze"
    log.table_name = "programas"
    log.affected_rows = 100
    log.started_at = started_at or datetime.datetime(2024, 1, 1, 10, 0, 0)
    log.finalized_at = finalized_at or datetime.datetime(2024, 1, 1, 10, 0, 5)
    log.operation_duration = 5
    log.operation_metadata = None
    return log


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def view():
    return AuditExecutionLogTableView.as_view()


class TestAuditExecutionLogTableView:
    @patch("audit.views.AuditExecutionLog.objects")
    def test_returns_200(self, mock_objects, factory, view):
        mock_objects.all.return_value.filter.return_value = mock_objects.all.return_value
        mock_objects.all.return_value.order_by.return_value = []

        request = factory.get("/audit/")
        response = view(request)

        assert response.status_code == 200

    @patch("audit.views.AuditExecutionLog.objects")
    def test_results_ordered_by_started_at_desc(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/")
        view(request)

        qs.order_by.assert_called_with("-started_at")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_status(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"status": "SUCCESS"})
        view(request)

        qs.filter.assert_any_call(status="SUCCESS")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_operation(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"operation": "INGEST"})
        view(request)

        qs.filter.assert_any_call(operation="INGEST")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_started_at_gte(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"started_at_gte": "2024-01-01T00:00:00"})
        view(request)

        assert qs.filter.called
        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert any("started_at__gte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_finalized_at_lte(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"finalized_at_lte": "2024-01-31T23:59:59"})
        view(request)

        assert qs.filter.called
        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert any("finalized_at__lte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_invalid_started_at_gte_ignored(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"started_at_gte": "not-a-date"})
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert not any("started_at__gte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_invalid_finalized_at_lte_ignored(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/", {"finalized_at_lte": "not-a-date"})
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert not any("finalized_at__lte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_no_filters_applied_when_no_params(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/audit/")
        view(request)

        qs.filter.assert_not_called()