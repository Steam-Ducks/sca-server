import datetime

import pytest
from django.utils import timezone

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)


@pytest.fixture
def tempo_em_memoria():
    now = timezone.now()

    programa = SilverPrograma(
        id=1,
        codigo_programa="PROG-001",
        nome_programa="Cloud",
        silver_ingested_at=now,
    )

    projeto = SilverProjeto(
        id=1,
        codigo_projeto="PROJ-001",
        nome_projeto="Migração AWS",
        custo_hora=420.00,
        silver_ingested_at=now,
    )
    projeto.programa = programa

    tarefa = SilverTarefaProjeto(
        id=1,
        codigo_tarefa="TAR-001",
        titulo="Arquitetura Cloud",
        responsavel="Cloud Architect",
        estimativa_horas=400,
        silver_ingested_at=now,
    )
    tarefa.projeto = projeto

    tempo = SilverTempoTarefa(
        id=1,
        usuario="Lucas Martins",
        data=datetime.date(2024, 3, 15),
        horas_trabalhadas=40.00,
        silver_ingested_at=now,
    )
    tempo.tarefa = tarefa
    tempo.custo_por_hora = 420.00
    tempo.custo_total = 40.00 * 420.00

    return tempo
