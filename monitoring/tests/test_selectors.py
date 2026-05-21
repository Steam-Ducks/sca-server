import datetime

import pytest
from unittest.mock import MagicMock, patch

from monitoring.selectors import get_execucoes_carga


@pytest.fixture
def mock_qs():
    qs = MagicMock()
    qs.filter.return_value = qs
    qs.order_by.return_value = qs
    return qs


class TestGetExecucoesCarga:
    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_returns_all_when_no_filters(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga()
        mock_model.objects.all.assert_called_once()
        mock_qs.order_by.assert_called_once_with("-iniciado_em")

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_filters_by_status(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga(status="FAILED")
        mock_qs.filter.assert_any_call(status="FAILED")

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_filters_by_data_inicio_date_object(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        d = datetime.date(2025, 1, 1)
        get_execucoes_carga(data_inicio=d)
        mock_qs.filter.assert_any_call(iniciado_em__date__gte=d)

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_filters_by_data_inicio_string(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga(data_inicio="2025-06-01")
        mock_qs.filter.assert_any_call(iniciado_em__date__gte=datetime.date(2025, 6, 1))

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_filters_by_data_fim_date_object(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        d = datetime.date(2025, 12, 31)
        get_execucoes_carga(data_fim=d)
        mock_qs.filter.assert_any_call(iniciado_em__date__lte=d)

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_filters_by_data_fim_string(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga(data_fim="2025-12-31")
        mock_qs.filter.assert_any_call(
            iniciado_em__date__lte=datetime.date(2025, 12, 31)
        )

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_no_status_filter_skips_status(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga(status=None)
        calls = [str(c) for c in mock_qs.filter.call_args_list]
        assert not any("status" in c for c in calls)

    @patch("monitoring.selectors.FatoExecucaoCarga")
    def test_ordered_by_iniciado_em_desc(self, mock_model, mock_qs):
        mock_model.objects.all.return_value = mock_qs
        get_execucoes_carga()
        mock_qs.order_by.assert_called_with("-iniciado_em")
