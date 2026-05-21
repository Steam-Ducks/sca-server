import pytest
from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory

from monitoring.views import ExecucaoCargaView


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def mock_execucoes():
    execucao = MagicMock()
    execucao.id = 1
    execucao.run_id = "uuid-1"
    execucao.fonte = "csv_upload"
    execucao.tabela = "programas"
    execucao.status = "SUCCESS"
    execucao.linhas_processadas = 10
    execucao.erros = 0
    execucao.avisos = 0
    execucao.detalhes_falha = None
    execucao.iniciado_em = "2025-01-15T10:00:00"
    execucao.finalizado_em = "2025-01-15T10:00:01"
    return [execucao]


class TestExecucaoCargaViewValidation:
    def test_invalid_status_returns_400(self, factory):
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/", {"status": "INVALIDO"})
        response = view(request)
        assert response.status_code == 400
        assert "error" in response.data

    def test_invalid_status_message_lists_valid_options(self, factory):
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/", {"status": "INVALIDO"})
        response = view(request)
        assert "FAILED" in response.data["error"]
        assert "PARTIAL" in response.data["error"]
        assert "SUCCESS" in response.data["error"]

    def test_invalid_data_inicio_returns_400(self, factory):
        view = ExecucaoCargaView.as_view()
        request = factory.get(
            "/api/monitoring/execucoes/", {"data_inicio": "not-a-date"}
        )
        response = view(request)
        assert response.status_code == 400
        assert "data_inicio" in response.data["error"]

    def test_invalid_data_fim_returns_400(self, factory):
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/", {"data_fim": "31-12-2025"})
        response = view(request)
        assert response.status_code == 400
        assert "data_fim" in response.data["error"]


class TestExecucaoCargaViewSuccess:
    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_returns_200(self, mock_serializer, mock_selector, factory):
        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/")
        response = view(request)
        assert response.status_code == 200

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_response_has_count_and_results(
        self, mock_serializer, mock_selector, factory
    ):
        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/")
        response = view(request)
        assert "count" in response.data
        assert "results" in response.data

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_count_matches_results_length(
        self, mock_serializer, mock_selector, factory
    ):
        mock_selector.return_value = []
        mock_serializer.return_value.data = [MagicMock(), MagicMock()]
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/")
        response = view(request)
        assert response.data["count"] == 2

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_empty_results_returns_200(self, mock_serializer, mock_selector, factory):
        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/")
        response = view(request)
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_status_filter_passed_to_selector(
        self, mock_serializer, mock_selector, factory
    ):
        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        request = factory.get("/api/monitoring/execucoes/", {"status": "FAILED"})
        view(request)
        mock_selector.assert_called_once()
        _, kwargs = mock_selector.call_args
        assert kwargs["status"] == "FAILED"

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_date_filters_passed_to_selector(
        self, mock_serializer, mock_selector, factory
    ):
        import datetime

        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        request = factory.get(
            "/api/monitoring/execucoes/",
            {"data_inicio": "2025-01-01", "data_fim": "2025-12-31"},
        )
        view(request)
        _, kwargs = mock_selector.call_args
        assert kwargs["data_inicio"] == datetime.date(2025, 1, 1)
        assert kwargs["data_fim"] == datetime.date(2025, 12, 31)

    @patch("monitoring.views.get_execucoes_carga")
    @patch("monitoring.views.FatoExecucaoCargaSerializer")
    def test_valid_statuses_accepted(self, mock_serializer, mock_selector, factory):
        mock_selector.return_value = []
        mock_serializer.return_value.data = []
        view = ExecucaoCargaView.as_view()
        for status in ("SUCCESS", "FAILED", "PARTIAL"):
            request = factory.get("/api/monitoring/execucoes/", {"status": status})
            response = view(request)
            assert response.status_code == 200


class TestExecucaoCargaViewUrl:
    def test_url_resolves(self):
        from django.urls import resolve

        resolver = resolve("/api/monitoring/execucoes/")
        assert resolver.view_name == "monitoring-execucoes"

    def test_url_reverses(self):
        from django.urls import reverse

        assert reverse("monitoring-execucoes") == "/api/monitoring/execucoes/"
