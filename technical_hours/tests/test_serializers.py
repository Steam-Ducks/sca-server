import datetime
from decimal import Decimal

from django.utils import timezone

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)
from technical_hours.serializers import TechnicalHoursTableSerializer


def _criar_tempo_em_memoria():
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
    # campos anotados pelo view (simulados manualmente)
    tempo.custo_por_hora = 420.00
    tempo.custo_total    = 40.00 * 420.00

    return tempo


def test_technical_hours_serializer_retorna_dados_corretos():
    tempo = _criar_tempo_em_memoria()

    serializer = TechnicalHoursTableSerializer(tempo)

    assert serializer.data["colaborador"]      == "Lucas Martins"
    assert serializer.data["funcao"]           == "Cloud Architect"
    assert serializer.data["projeto"]          == "Migração AWS"
    assert serializer.data["programa"]         == "Cloud"
    assert serializer.data["horas_trabalhadas"] == Decimal("40.00")
    assert serializer.data["custo_por_hora"]   == Decimal("420.00")
    assert serializer.data["custo_total"]      == Decimal("16800.00")
    assert serializer.data["periodo"]          == "2024-03"
    assert serializer.data["tarefa"]           == "Arquitetura Cloud"


def test_technical_hours_serializer_periodo_none_quando_data_nula():
    tempo = _criar_tempo_em_memoria()
    tempo.data = None

    serializer = TechnicalHoursTableSerializer(tempo)

    assert serializer.data["periodo"] is None


def test_technical_hours_serializer_campos_none_quando_sem_tarefa():
    tempo = _criar_tempo_em_memoria()
    tempo.tarefa = None

    serializer = TechnicalHoursTableSerializer(tempo)

    assert serializer.data["funcao"]   is None
    assert serializer.data["projeto"]  is None
    assert serializer.data["programa"] is None
    assert serializer.data["tarefa"]   is None


def test_technical_hours_serializer_campos_none_quando_sem_programa():
    tempo = _criar_tempo_em_memoria()
    tempo.tarefa.projeto.programa = None

    serializer = TechnicalHoursTableSerializer(tempo)

    assert serializer.data["programa"] is None


def test_technical_hours_serializer_retorna_todos_os_campos():
    tempo = _criar_tempo_em_memoria()

    serializer = TechnicalHoursTableSerializer(tempo)

    expected_fields = {
        "id", "colaborador", "funcao", "projeto", "programa",
        "horas_trabalhadas", "custo_por_hora", "custo_total",
        "periodo", "tarefa",
    }
    assert set(serializer.data.keys()) == expected_fields