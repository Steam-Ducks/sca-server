import datetime
from types import SimpleNamespace

from monitoring.serializers import FatoExecucaoCargaSerializer


def _execucao(**kwargs):
    defaults = dict(
        id=1,
        run_id="uuid-1",
        fonte="csv_upload",
        tabela="materiais",
        tipo_processo="COMPLETA",
        status="SUCCESS",
        linhas_processadas=10,
        erros=0,
        avisos=0,
        detalhes_falha=None,
        iniciado_em=datetime.datetime(2025, 1, 1, 10, 0, 0),
        finalizado_em=datetime.datetime(2025, 1, 1, 10, 0, 42),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_duracao_segundos_calculated_correctly():
    obj = _execucao(
        iniciado_em=datetime.datetime(2025, 1, 1, 10, 0, 0),
        finalizado_em=datetime.datetime(2025, 1, 1, 10, 0, 42),
    )
    assert FatoExecucaoCargaSerializer(obj).data["duracao_segundos"] == 42


def test_duracao_segundos_none_when_finalizado_em_null():
    obj = _execucao(finalizado_em=None)
    assert FatoExecucaoCargaSerializer(obj).data["duracao_segundos"] is None


def test_duracao_segundos_zero_when_same_timestamps():
    ts = datetime.datetime(2025, 6, 1, 12, 0, 0)
    obj = _execucao(iniciado_em=ts, finalizado_em=ts)
    assert FatoExecucaoCargaSerializer(obj).data["duracao_segundos"] == 0


def test_duracao_segundos_is_integer():
    obj = _execucao(
        iniciado_em=datetime.datetime(2025, 1, 1, 10, 0, 0),
        finalizado_em=datetime.datetime(2025, 1, 1, 10, 1, 30),
    )
    assert isinstance(FatoExecucaoCargaSerializer(obj).data["duracao_segundos"], int)


def test_duracao_segundos_multi_minute():
    obj = _execucao(
        iniciado_em=datetime.datetime(2025, 1, 1, 10, 0, 0),
        finalizado_em=datetime.datetime(2025, 1, 1, 10, 45, 0),
    )
    assert FatoExecucaoCargaSerializer(obj).data["duracao_segundos"] == 2700


def test_tipo_processo_completa_serialized():
    obj = _execucao(tipo_processo="COMPLETA")
    assert FatoExecucaoCargaSerializer(obj).data["tipo_processo"] == "COMPLETA"


def test_tipo_processo_incremental_serialized():
    obj = _execucao(tipo_processo="INCREMENTAL")
    assert FatoExecucaoCargaSerializer(obj).data["tipo_processo"] == "INCREMENTAL"


def test_all_expected_fields_present():
    data = FatoExecucaoCargaSerializer(_execucao()).data
    expected = {
        "id",
        "run_id",
        "fonte",
        "tabela",
        "tipo_processo",
        "status",
        "linhas_processadas",
        "erros",
        "avisos",
        "duracao_segundos",
        "detalhes_falha",
        "iniciado_em",
        "finalizado_em",
    }
    assert expected == set(data.keys())
