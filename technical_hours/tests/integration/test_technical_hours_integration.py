"""
Conjunto de integração: Technical Hours (Horas Técnicas)

Funções do conjunto:
    get_queryset (views.py)             — aplica filtros ao ORM
    TechnicalHoursTableView (views.py)  — endpoint GET /api/horas-tecnicas/
    TechnicalHoursTableSerializer       — serializa horas técnicas

FIX: URL correta é /api/horas-tecnicas/ (não /api/technical-hours/)
Fonte: technical_hours/urls.py
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

# Skip when PostgreSQL is unavailable (SQLite CI environment).
# To run locally: export DB_HOST=postgres (or your host) before pytest.
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver/gold schemas — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


# URL correta conforme technical_hours/urls.py
HORAS_URL = "/api/horas-tecnicas/"


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
        custo_hora=250.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def tarefa(db, projeto):
    return SilverTarefaProjeto.objects.create(
        id=800,
        codigo_tarefa="TAR-800",
        projeto=projeto,
        titulo="Implementação do módulo",
        estimativa_horas=80,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def horas_marco(db, tarefa):
    SilverTempoTarefa.objects.create(
        id=800,
        tarefa=tarefa,
        usuario="dev1@sca.com",
        data=date(2024, 3, 5),
        horas_trabalhadas=8.0,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    SilverTempoTarefa.objects.create(
        id=801,
        tarefa=tarefa,
        usuario="dev1@sca.com",
        data=date(2024, 3, 6),
        horas_trabalhadas=7.5,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


class TestTechnicalHoursTableIntegration:
    """
    CT-INT-TECH-01
    Conjunto: get_queryset (filtros) + TechnicalHoursTableView + serializer
    """

    def test_lista_retorna_200(self, api_client):
        response = api_client.get(HORAS_URL)
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self, api_client):
        response = api_client.get(HORAS_URL)
        assert response.data == []

    def test_retorna_horas_reais_do_banco(self, api_client, horas_marco):
        response = api_client.get(HORAS_URL)
        assert len(response.data) >= 2

    def test_filtro_por_periodo_retorna_apenas_horas_do_mes(self, api_client, tarefa):
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
        assert len(response.data) >= 1
        for item in response.data:
            assert item.get("periodo", "").startswith("2024-03")

    def test_filtro_por_data_inicio_e_fim(self, api_client, tarefa):
        SilverTempoTarefa.objects.create(
            id=820,
            tarefa=tarefa,
            usuario="dev3@sca.com",
            data=date(2024, 4, 1),
            horas_trabalhadas=5.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )
        SilverTempoTarefa.objects.create(
            id=821,
            tarefa=tarefa,
            usuario="dev3@sca.com",
            data=date(2024, 6, 1),
            horas_trabalhadas=50.0,
            silver_ingested_at=datetime.now(tz=timezone.utc),
        )

        response = api_client.get(
            f"{HORAS_URL}?data_inicio=2024-04-01&data_fim=2024-04-30"
        )
        assert response.status_code == 200
        assert len(response.data) >= 1
        for item in response.data:
            assert item.get("periodo", "").startswith("2024-04")

    def test_data_inicio_posterior_a_data_fim_retorna_400(self, api_client):
        # CTI-06 (adicional): data_inicio > data_fim → 400 ValidationError
        # Valida: _filters_from_date_range levanta erro propagado pela view
        response = api_client.get(
            f"{HORAS_URL}?data_inicio=2024-06-01&data_fim=2024-01-01"
        )
        assert response.status_code == 400
