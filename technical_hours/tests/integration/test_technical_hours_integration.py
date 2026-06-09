"""
Conjunto de integração: Technical Hours (atualizado)

Funções do conjunto:
    TechnicalHoursTableView    GET /api/horas-tecnicas/
    TechnicalHoursKpiView      GET /api/horas-tecnicas/kpis/
    TechnicalHoursTemporalView GET /api/horas-tecnicas/temporal/
    TechnicalHoursTablePeriodoView GET /api/horas-tecnicas/periodo/<YYYY-MM>/
    TechnicalHoursTableSerializer + filtros ORM
"""

import os
import pytest
from datetime import date, datetime, timezone

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver schema — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]

HORAS_URL = "/api/horas-tecnicas/"
KPIS_URL = "/api/horas-tecnicas/kpis/"
TEMPO_URL = "/api/horas-tecnicas/temporal/"


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=800,
        codigo_programa="TECH",
        nome_programa="Tecnologia",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=800,
        codigo_projeto="PROJ-800",
        nome_projeto="Sistema SCADA",
        programa=programa,
        custo_hora=300.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def tarefa(db, projeto):
    return SilverTarefaProjeto.objects.create(
        id=800,
        codigo_tarefa="TAR-800",
        titulo="Desenvolvimento",
        projeto=projeto,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def horas_marco(db, tarefa):
    """2 registros em março/2024."""
    SilverTempoTarefa.objects.create(
        id=800,
        tarefa=tarefa,
        usuario="dev1@sca.com",
        data=date(2024, 3, 10),
        horas_trabalhadas=8.0,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    SilverTempoTarefa.objects.create(
        id=801,
        tarefa=tarefa,
        usuario="dev2@sca.com",
        data=date(2024, 3, 15),
        horas_trabalhadas=6.0,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


# ── CTI: TechnicalHoursTableView ─────────────────────────────────────────────


class TestTechnicalHoursTableIntegration:
    """
    CTI-01 ao CTI-06
    Conjunto: TechnicalHoursTableView + TechnicalHoursTableSerializer
    """

    def test_lista_retorna_200(self, api_client):
        # CTI-01 (mínimo): banco vazio → 200
        response = api_client.get(HORAS_URL)
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self, api_client):
        # CTI-02 (mínimo): banco vazio → lista vazia
        response = api_client.get(HORAS_URL)
        assert response.data == []

    def test_retorna_horas_reais_do_banco(self, api_client, horas_marco):
        # CTI-03 (mínimo): apontamentos inseridos → aparecem na resposta
        response = api_client.get(HORAS_URL)
        assert len(response.data) >= 2

    def test_campos_do_serializer_presentes(self, api_client, horas_marco):
        # CTI-04 (mínimo): campos corretos chegam ao frontend
        response = api_client.get(HORAS_URL)
        item = response.data[0]
        for campo in [
            "id",
            "colaborador",
            "projeto",
            "programa",
            "horas_trabalhadas",
            "custo_total",
            "periodo",
        ]:
            assert campo in item, f"Campo ausente: {campo}"

    def test_filtro_por_periodo_retorna_apenas_horas_do_mes(self, api_client, tarefa):
        # CTI-05 (mínimo): ?periodo=2024-03 → só março retorna
        SilverTempoTarefa.objects.create(
            id=810,
            tarefa=tarefa,
            usuario="dev2@sca.com",
            data=date(2024, 3, 15),
            horas_trabalhadas=6.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=811,
            tarefa=tarefa,
            usuario="dev2@sca.com",
            data=date(2024, 7, 10),
            horas_trabalhadas=99.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get(f"{HORAS_URL}?periodo=2024-03")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert str(response.data[0]["periodo"]).startswith("2024-03")

    def test_data_inicio_posterior_a_data_fim_retorna_400(self, api_client):
        # CTI-06 (adicional): data_inicio > data_fim → 400
        response = api_client.get(
            f"{HORAS_URL}?data_inicio=2024-06-01&data_fim=2024-01-01"
        )
        assert response.status_code == 400


# ── CTI: TechnicalHoursKpiView ────────────────────────────────────────────────


class TestTechnicalHoursKpiIntegration:
    """
    CTI-07 ao CTI-09
    Conjunto: TechnicalHoursKpiView + KPI aggregation
    GET /api/horas-tecnicas/kpis/
    """

    def test_kpis_retornam_200(self, api_client):
        # CTI-07 (mínimo): banco vazio → 200
        response = api_client.get(KPIS_URL)
        assert response.status_code == 200

    def test_kpis_contem_campos_esperados(self, api_client):
        # CTI-08 (mínimo): campos custo_total e total_horas presentes
        response = api_client.get(KPIS_URL)
        assert "custo_total" in response.data
        assert "total_horas" in response.data

    def test_kpis_somam_horas_reais(self, api_client, horas_marco):
        # CTI-09 (mínimo): 8h + 6h × R$300/h → custo_total e total_horas corretos
        response = api_client.get(KPIS_URL)
        assert float(response.data["total_horas"]) == 14.0
        assert float(response.data["custo_total"]) == 300.0 * 14.0


# ── CTI: TechnicalHoursTemporalView ──────────────────────────────────────────


class TestTechnicalHoursTemporalIntegration:
    """
    CTI-10 ao CTI-12
    Conjunto: TechnicalHoursTemporalView — série histórica por período
    GET /api/horas-tecnicas/temporal/
    """

    def test_temporal_retorna_200(self, api_client):
        # CTI-10 (mínimo): banco vazio → 200
        response = api_client.get(TEMPO_URL)
        assert response.status_code == 200

    def test_temporal_e_lista(self, api_client):
        # CTI-11 (mínimo): response é sempre lista
        response = api_client.get(TEMPO_URL)
        assert isinstance(response.data, list)

    def test_temporal_agrupa_por_periodo(self, api_client, tarefa):
        # CTI-12 (mínimo): horas em meses diferentes → um item por mês
        SilverTempoTarefa.objects.create(
            id=820,
            tarefa=tarefa,
            usuario="dev@sca.com",
            data=date(2024, 1, 10),
            horas_trabalhadas=10.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=821,
            tarefa=tarefa,
            usuario="dev@sca.com",
            data=date(2024, 3, 10),
            horas_trabalhadas=5.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get(TEMPO_URL)
        periodos = [item["periodo"] for item in response.data]
        assert "2024-01" in periodos
        assert "2024-03" in periodos
