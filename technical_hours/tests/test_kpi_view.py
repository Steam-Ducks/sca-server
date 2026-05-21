import pytest
from unittest.mock import MagicMock, patch

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


def test_kpi_retorna_200(api_client):
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(URL)
        assert response.status_code == 200


def test_kpi_retorna_todos_os_campos(api_client):
    """CT01: todos os 4 indicadores devem estar presentes na resposta."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(URL)
        assert "custo_total" in response.data
        assert "total_horas" in response.data
        assert "custo_medio" in response.data
        assert "registros" in response.data


def test_kpi_calcula_valores_corretamente(api_client):
    """CT01: valores derivados do queryset anotado."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=40.0, soma_custo=16800.0, registros=1),
    ):
<<<<<<< HEAD
        response = api_client.get(URL)
        assert response.data["total_horas"] == 40.0
        assert response.data["custo_total"] == 16800.0
=======
        response = APIClient().get(URL)
        assert response.data["total_horas"] == pytest.approx(40.0)
        assert response.data["custo_total"] == pytest.approx(16800.0)
>>>>>>> 9e90797c56ff7b00c563e37e5eaafc8d008674dc
        assert response.data["registros"] == 1


# ── CT04: formatação com precisão de 2 casas decimais ────────────────────────


def test_kpi_calcula_custo_medio(api_client):
    """CT04: custo_medio = custo_total / total_horas."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=40.0, soma_custo=16800.0),
    ):
<<<<<<< HEAD
        response = api_client.get(URL)
        assert response.data["custo_medio"] == 420.0
=======
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == pytest.approx(420.0)
>>>>>>> 9e90797c56ff7b00c563e37e5eaafc8d008674dc


def test_kpi_arredonda_para_duas_casas(api_client):
    """CT04: divisão com dízima arredondada para 2 casas decimais."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=3.0, soma_custo=10.0),
    ):
<<<<<<< HEAD
        response = api_client.get(URL)
        assert response.data["custo_medio"] == 3.33
=======
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == pytest.approx(3.33)
>>>>>>> 9e90797c56ff7b00c563e37e5eaafc8d008674dc


# ── Casos extremos ───────────────────────────────────────────────────────────


def test_kpi_sem_dados_retorna_zeros(api_client):
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=None, soma_custo=None, registros=0),
    ):
        response = api_client.get(URL)
        assert response.status_code == 200
        assert response.data["custo_total"] == pytest.approx(0.0)
        assert response.data["total_horas"] == pytest.approx(0.0)
        assert response.data["custo_medio"] == pytest.approx(0.0)
        assert response.data["registros"] == 0


def test_kpi_custo_medio_zero_quando_sem_horas(api_client):
    """Não divide por zero quando total_horas é 0."""
    with patch.object(
        TechnicalHoursKpiView,
        "get_queryset",
        return_value=_mock_qs(total_horas=0.0, soma_custo=0.0),
    ):
<<<<<<< HEAD
        response = api_client.get(URL)
        assert response.data["custo_medio"] == 0.0
=======
        response = APIClient().get(URL)
        assert response.data["custo_medio"] == pytest.approx(0.0)
>>>>>>> 9e90797c56ff7b00c563e37e5eaafc8d008674dc


# ── CT03: filtros respeitados pelo endpoint ──────────────────────────────────


def test_kpi_aceita_filtro_periodo(api_client):
    """CT03: filtro por período não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(f"{URL}?periodo=2024-03")
        assert response.status_code == 200


def test_kpi_aceita_filtro_data_range(api_client):
    """CT03: filtro por intervalo de datas não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(f"{URL}?data_inicio=2024-01-01&data_fim=2024-03-31")
        assert response.status_code == 200


def test_kpi_aceita_filtro_ano_mes(api_client):
    """CT03: filtro por ano e mês não causa erro."""
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(f"{URL}?ano=2024&mes=3")
        assert response.status_code == 200


def test_kpi_aceita_filtro_programa(api_client):
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(f"{URL}?programa=Cloud")
        assert response.status_code == 200


def test_kpi_aceita_filtro_projeto(api_client):
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(f"{URL}?projeto=Migracao AWS")
        assert response.status_code == 200


def test_kpi_aceita_filtros_combinados_programa_e_projeto(api_client):
    with patch.object(TechnicalHoursKpiView, "get_queryset", return_value=_mock_qs()):
        response = api_client.get(
            f"{URL}?programa=Cloud&projeto=Migracao AWS&periodo=2024-03"
        )
        assert response.status_code == 200


def test_kpi_periodo_invalido_retorna_400(api_client):
    response = api_client.get(f"{URL}?periodo=invalido")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_kpi_data_inicio_invalida_retorna_400(api_client):
    response = api_client.get(f"{URL}?data_inicio=nao-e-data")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_kpi_data_inicio_posterior_data_fim_retorna_400(api_client):
    response = api_client.get(f"{URL}?data_inicio=2024-03-31&data_fim=2024-01-01")
    assert response.status_code == 400
    assert "data_inicio" in response.data


def test_kpi_ano_nao_numerico_retorna_400(api_client):
    response = api_client.get(f"{URL}?ano=abc")
    assert response.status_code == 400
    assert "ano" in response.data
