from decimal import Decimal

from technical_hours.serializers import TechnicalHoursTableSerializer


def test_technical_hours_serializer_retorna_dados_corretos(tempo_em_memoria):
    serializer = TechnicalHoursTableSerializer(tempo_em_memoria)

    assert serializer.data["colaborador"] == "Lucas Martins"
    assert serializer.data["funcao"] == "Cloud Architect"
    assert serializer.data["projeto"] == "Migração AWS"
    assert serializer.data["programa"] == "Cloud"
    assert serializer.data["horas_trabalhadas"] == Decimal("40.00")
    assert serializer.data["custo_por_hora"] == Decimal("420.00")
    assert serializer.data["custo_total"] == Decimal("16800.00")
    assert serializer.data["periodo"] == "2024-03"
    assert serializer.data["tarefa"] == "Arquitetura Cloud"


def test_technical_hours_serializer_periodo_none_quando_data_nula(tempo_em_memoria):
    tempo_em_memoria.data = None

    serializer = TechnicalHoursTableSerializer(tempo_em_memoria)

    assert serializer.data["periodo"] is None


def test_technical_hours_serializer_campos_none_quando_sem_tarefa(tempo_em_memoria):
    tempo_em_memoria.tarefa = None

    serializer = TechnicalHoursTableSerializer(tempo_em_memoria)

    assert serializer.data["funcao"] is None
    assert serializer.data["projeto"] is None
    assert serializer.data["programa"] is None
    assert serializer.data["tarefa"] is None


def test_technical_hours_serializer_campos_none_quando_sem_programa(tempo_em_memoria):
    tempo_em_memoria.tarefa.projeto.programa = None

    serializer = TechnicalHoursTableSerializer(tempo_em_memoria)

    assert serializer.data["programa"] is None


def test_technical_hours_serializer_retorna_todos_os_campos(tempo_em_memoria):
    serializer = TechnicalHoursTableSerializer(tempo_em_memoria)

    expected_fields = {
        "id",
        "colaborador",
        "funcao",
        "projeto",
        "programa",
        "horas_trabalhadas",
        "custo_por_hora",
        "custo_total",
        "periodo",
        "tarefa",
    }
    assert set(serializer.data.keys()) == expected_fields
