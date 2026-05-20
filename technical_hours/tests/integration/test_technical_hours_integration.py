"""
Conjunto de integração: Technical Hours (Horas Técnicas)

Funções do conjunto:
    _parse_date (views.py)              — valida e converte data string
    _parse_periodo (views.py)           — converte YYYY-MM em intervalo
    get_queryset (views.py)             — aplica filtros ao ORM
    TechnicalHoursTableView (views.py)  — GET /api/technical-hours/
    TechnicalHoursTableSerializer       — serializa horas técnicas

O conjunto valida que os filtros de data/período/programa/projeto
produzem o conjunto correto de registros a partir dos dados reais do banco.
"""

import pytest
from datetime import date, datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=800, codigo_programa="TECH", nome_programa="Tecnologia",
        status="Em andamento", silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=800, codigo_projeto="PROJ-800", nome_projeto="Sistema SCADA",
        programa=programa, custo_hora=250.0, status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def tarefa(db, projeto):
    return SilverTarefaProjeto.objects.create(
        id=800, codigo_tarefa="TAR-800", projeto=projeto,
        titulo="Implementação do módulo", estimativa_horas=80,
        status="Em andamento", silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def horas_marco(db, tarefa):
    SilverTempoTarefa.objects.create(
        id=800, tarefa=tarefa, usuario="dev1@sca.com",
        data=date(2024, 3, 5), horas_trabalhadas=8.0,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    SilverTempoTarefa.objects.create(
        id=801, tarefa=tarefa, usuario="dev1@sca.com",
        data=date(2024, 3, 6), horas_trabalhadas=7.5,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestTechnicalHoursTableIntegration:
    """
    CT-INT-TECH-01
    Conjunto: get_queryset (filtros) + TechnicalHoursTableView + serializer
    """

    def test_lista_retorna_200(self):
        response = APIClient().get("/api/technical-hours/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self):
        response = APIClient().get("/api/technical-hours/")
        assert response.data == []

    def test_retorna_horas_reais_do_banco(self, horas_marco):
        response = APIClient().get("/api/technical-hours/")
        assert len(response.data) >= 2

    def test_filtro_por_periodo_retorna_apenas_horas_do_mes(
        self, tarefa
    ):
        # Horas em março — devem aparecer
        SilverTempoTarefa.objects.create(
            id=810, tarefa=tarefa, usuario="dev2@sca.com",
            data=date(2024, 3, 15), horas_trabalhadas=6.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        # Horas em julho — NÃO devem aparecer
        SilverTempoTarefa.objects.create(
            id=811, tarefa=tarefa, usuario="dev2@sca.com",
            data=date(2024, 7, 10), horas_trabalhadas=99.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/technical-hours/?periodo=2024-03")

        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            data_str = item.get("data", "")
            assert data_str.startswith("2024-03"), (
                f"Horas fora do período encontradas: {data_str}"
            )

    def test_filtro_por_data_inicio_e_fim(self, tarefa):
        SilverTempoTarefa.objects.create(
            id=820, tarefa=tarefa, usuario="dev3@sca.com",
            data=date(2024, 4, 1), horas_trabalhadas=5.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=821, tarefa=tarefa, usuario="dev3@sca.com",
            data=date(2024, 6, 1), horas_trabalhadas=50.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get(
            "/api/technical-hours/?data_inicio=2024-04-01&data_fim=2024-04-30"
        )

        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            assert item["data"].startswith("2024-04")

    def test_data_inicio_posterior_a_data_fim_retorna_400(self):
        response = APIClient().get(
            "/api/technical-hours/?data_inicio=2024-06-01&data_fim=2024-01-01"
        )
        assert response.status_code == 400
