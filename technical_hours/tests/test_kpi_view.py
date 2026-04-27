from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient

from technical_hours.views import TechnicalHoursKpiView

URL = "/api/horas-tecnicas/kpis/"


def _mock_qs(total_horas=40.0, soma_custo=16800.0, registros=1):
    mock = MagicMock()
    mock.aggregate.return_value = {
        "total_horas": total_horas,
        "soma_custo": soma_custo,
        "registros": registros,
    }
    return mock


# ── CT01: indicadores presentes e corretos ───────────────────────────────────


def test_kpi_retorna_200():
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = APIClient().get(URL)
        assert response.status_code == 200


def test_kpi_retorna_todos_os_campos():
    """CT01: todos os 4 indicadores devem estar presentes na resposta."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = APIClient().get(URL)
        assert "custo_total" in response.data
        assert "total_horas" in response.data
        assert "custo_medio" in response.data
        assert "registros" in response.data


def test_kpi_calcula_valores_corretamente():
    """CT01: valores derivados do queryset anotado."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=40.0, soma_custo=16800.0, registros=1),
    ):
        response = APIClient().get(URL)
        assert response.data["total_horas"] == 40.0
        assert response.data["custo_total"] == 16800.0
        assert response.data["registros"] == 1


# ── CT04: formatação com precisão de 2 casas decimais ────────────────────────


def test_kpi_calcula_custo_medio():
    """CT04: custo_medio = custo_total / total_horas."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=40.0, soma_custo=16800.0),
    ):
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == 420.0


def test_kpi_arredonda_para_duas_casas():
    """CT04: divisão com dízima arredondada para 2 casas decimais."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=3.0, soma_custo=10.0),
    ):
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == 3.33


# ── Casos extremos ───────────────────────────────────────────────────────────


def test_kpi_sem_dados_retorna_zeros():
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=None, soma_custo=None, registros=0),
    ):
        response = APIClient().get(URL)
        assert response.status_code == 200
        assert response.data["custo_total"] == 0.0
        assert response.data["total_horas"] == 0.0
        assert response.data["custo_medio"] == 0.0
        assert response.data["registros"] == 0


def test_kpi_custo_medio_zero_quando_sem_horas():
    """Não divide por zero quando total_horas é 0."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=0.0, soma_custo=0.0),
    ):
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == 0.0


# ── CT03: filtros respeitados pelo endpoint ──────────────────────────────────


def test_kpi_aceita_filtro_periodo():
    """CT03: filtro por período não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = APIClient().get(f"{URL}?periodo=2024-03")
        assert response.status_code == 200


def test_kpi_aceita_filtro_data_range():
    """CT03: filtro por intervalo de datas não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = APIClient().get(f"{URL}?data_inicio=2024-01-01&data_fim=2024-03-31")
        assert response.status_code == 200


def test_kpi_aceita_filtro_ano_mes():
    """CT03: filtro por ano e mês não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = APIClient().get(f"{URL}?ano=2024&mes=3")
        assert response.status_code == 200


def test_kpi_periodo_invalido_retorna_400():
    response = APIClient().get(f"{URL}?periodo=invalido")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_kpi_data_inicio_invalida_retorna_400():
    response = APIClient().get(f"{URL}?data_inicio=nao-e-data")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_kpi_data_inicio_posterior_data_fim_retorna_400():
    response = APIClient().get(f"{URL}?data_inicio=2024-03-31&data_fim=2024-01-01")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_kpi_ano_nao_numerico_retorna_400():
    response = APIClient().get(f"{URL}?ano=abc")
    assert response.status_code == 400
    assert "ano" in response.data
