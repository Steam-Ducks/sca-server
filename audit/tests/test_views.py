import pytest
from unittest.mock import patch, MagicMock
import datetime
from rest_framework.test import APIRequestFactory

from audit.views import AuditExecutionLogTableView


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def view():
    return AuditExecutionLogTableView.as_view()


class TestAuditExecutionLogTableView:
    @patch("audit.views.AuditExecutionLog.objects")
    def test_returns_200(self, mock_objects, factory, view):
        mock_objects.all.return_value.filter.return_value = (
            mock_objects.all.return_value
        )
        mock_objects.all.return_value.order_by.return_value = []

        request = factory.get("/api/audit/")
        response = view(request)

        assert response.status_code == 200

    @patch("audit.views.AuditExecutionLog.objects")
    def test_results_ordered_by_started_at_desc(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/")
        view(request)

        qs.order_by.assert_called_with("-started_at")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_status(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"status": "SUCCESS"})
        view(request)

        qs.filter.assert_any_call(status="SUCCESS")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_operation(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"operation": "INGEST"})
        view(request)

        qs.filter.assert_any_call(operation="INGEST")

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_started_at_gte(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"started_at_gte": "2024-01-01T00:00:00"})
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

        request = factory.get(
            "/api/audit/", {"finalized_at_lte": "2024-01-31T23:59:59"}
        )
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

        request = factory.get("/api/audit/", {"started_at_gte": "not-a-date"})
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert not any("started_at__gte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_invalid_finalized_at_lte_ignored(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"finalized_at_lte": "not-a-date"})
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert not any("finalized_at__lte" in kw for kw in call_kwargs)

    @patch("audit.views.AuditExecutionLog.objects")
    def test_no_filters_applied_when_no_params(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/")
        view(request)

        qs.filter.assert_not_called()

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_programa_from_operation_metadata(
        self, mock_objects, factory, view
    ):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"programa": "Cloud"})
        view(request)

        calls_as_text = [str(call) for call in qs.filter.call_args_list]
        assert any(
            "operation_metadata__programa__iexact" in call for call in calls_as_text
        )
        assert any(
            "operation_metadata__nome_programa__iexact" in call
            for call in calls_as_text
        )

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_projeto_from_operation_metadata(
        self, mock_objects, factory, view
    ):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"projeto": "Migracao AWS"})
        view(request)

        calls_as_text = [str(call) for call in qs.filter.call_args_list]
        assert any(
            "operation_metadata__projeto__iexact" in call for call in calls_as_text
        )
        assert any(
            "operation_metadata__nome_projeto__iexact" in call for call in calls_as_text
        )

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_periodo(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get("/api/audit/", {"periodo": "2024-03"})
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert {
            "started_at__date__gte": datetime.date(2024, 3, 1),
            "started_at__date__lte": datetime.date(2024, 3, 31),
        } in call_kwargs

    @patch("audit.views.AuditExecutionLog.objects")
    def test_filters_by_data_inicio_and_data_fim(self, mock_objects, factory, view):
        qs = MagicMock()
        mock_objects.all.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = []

        request = factory.get(
            "/api/audit/",
            {"data_inicio": "2024-03-01", "data_fim": "2024-03-31"},
        )
        view(request)

        call_kwargs = [call.kwargs for call in qs.filter.call_args_list]
        assert {"started_at__date__gte": datetime.date(2024, 3, 1)} in call_kwargs
        assert {"started_at__date__lte": datetime.date(2024, 3, 31)} in call_kwargs

    def test_periodo_invalido_retorna_400(self, factory, view):
        request = factory.get("/api/audit/", {"periodo": "2024-13"})
        response = view(request)

        assert response.status_code == 400
        assert "periodo" in response.data

    def test_data_inicio_invalida_retorna_400(self, factory, view):
        request = factory.get("/api/audit/", {"data_inicio": "31-03-2024"})
        response = view(request)

        assert response.status_code == 400
        assert "data_inicio" in response.data
