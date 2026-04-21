import datetime
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from sca_data.models import SilverPrograma, SilverProjeto, SilverTarefaProjeto, SilverTempoTarefa
from technical_hours.views import TechnicalHoursTablePeriodoView

URL = "/api/horas-tecnicas/periodo/"


def _make_tempo(
    id=1,
    usuario="Lucas Martins",
    data=datetime.date(2024, 3, 15),
    horas_trabalhadas=40.00,
    custo_hora=420.00,
    nome_projeto="Migração AWS",
    nome_programa="Cloud",
    responsavel="Cloud Architect",
    titulo_tarefa="Arquitetura Cloud",
):
    now = timezone.now()
    programa = SilverPrograma(
        id=id, codigo_programa=f"P-{id}", nome_programa=nome_programa, silver_ingested_at=now
    )
    projeto = SilverProjeto(
        id=id, codigo_projeto=f"PR-{id}", nome_projeto=nome_projeto,
        custo_hora=custo_hora, silver_ingested_at=now,
    )
    projeto.programa = programa
    tarefa = SilverTarefaProjeto(
        id=id, codigo_tarefa=f"TAR-{id}", titulo=titulo_tarefa,
        responsavel=responsavel, estimativa_horas=400, silver_ingested_at=now,
    )
    tarefa.projeto = projeto
    tempo = SilverTempoTarefa(
        id=id, usuario=usuario, data=data,
        horas_trabalhadas=horas_trabalhadas, silver_ingested_at=now,
    )
    tempo.tarefa = tarefa
    tempo.custo_por_hora = custo_hora
    tempo.custo_total = horas_trabalhadas * custo_hora
    return tempo


# ---------------------------------------------------------------------------
# Testes do endpoint dedicado /api/horas-tecnicas/periodo/<YYYY-MM>/
# ---------------------------------------------------------------------------


def test_periodo_endpoint_retorna_200():
    with patch.object(TechnicalHoursTablePeriodoView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get(f"{URL}2024-03/")
        assert response.status_code == 200


def test_periodo_endpoint_retorna_lista():
    tempo = _make_tempo()
    with patch.object(TechnicalHoursTablePeriodoView, "get_queryset", return_value=[tempo]):
        client = APIClient()
        response = client.get(f"{URL}2024-03/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_periodo_endpoint_retorna_campos_corretos():
    tempo = _make_tempo()
    with patch.object(TechnicalHoursTablePeriodoView, "get_queryset", return_value=[tempo]):
        client = APIClient()
        response = client.get(f"{URL}2024-03/")
        item = response.data[0]
        assert item["colaborador"] == "Lucas Martins"
        assert item["funcao"] == "Cloud Architect"
        assert item["projeto"] == "Migração AWS"
        assert item["programa"] == "Cloud"
        assert item["horas_trabalhadas"] == Decimal("40.00")
        assert item["custo_por_hora"] == Decimal("420.00")
        assert item["custo_total"] == Decimal("16800.00")
        assert item["periodo"] == "2024-03"
        assert item["tarefa"] == "Arquitetura Cloud"


def test_periodo_endpoint_lista_vazia():
    with patch.object(TechnicalHoursTablePeriodoView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get(f"{URL}2024-03/")
        assert response.status_code == 200
        assert response.data == []


def test_periodo_endpoint_periodo_invalido_retorna_400():
    client = APIClient()
    response = client.get(f"{URL}2024-13/")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_endpoint_formato_errado_retorna_400():
    client = APIClient()
    for bad in ["202403", "abcd-ef", "2024-3"]:
        response = client.get(f"{URL}{bad}/")
        assert response.status_code == 400, f"Esperado 400 para '{bad}'"


def test_periodo_endpoint_com_barra_retorna_404():
    client = APIClient()
    response = client.get("/api/horas-tecnicas/periodo/2024/03/")
    assert response.status_code == 404


def test_periodo_endpoint_dezembro_ultimo_dia_correto():
    view = TechnicalHoursTablePeriodoView()
    inicio, fim = view._parse_periodo("2024-12")
    assert inicio == datetime.date(2024, 12, 1)
    assert fim == datetime.date(2024, 12, 31)


def test_periodo_endpoint_janeiro_ultimo_dia_correto():
    view = TechnicalHoursTablePeriodoView()
    inicio, fim = view._parse_periodo("2024-01")
    assert inicio == datetime.date(2024, 1, 1)
    assert fim == datetime.date(2024, 1, 31)


def test_periodo_endpoint_multiplos_registros():
    tempo1 = _make_tempo(id=1)
    tempo2 = _make_tempo(
        id=2, usuario="Ana Oliveira", data=datetime.date(2024, 3, 20),
        horas_trabalhadas=52.00, custo_hora=250.00,
        nome_projeto="Portal Web", nome_programa="Desenvolvimento",
        responsavel="Full Stack Dev", titulo_tarefa="Desenvolvimento",
    )
    with patch.object(
        TechnicalHoursTablePeriodoView, "get_queryset", return_value=[tempo1, tempo2]
    ):
        client = APIClient()
        response = client.get(f"{URL}2024-03/")
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["colaborador"] == "Lucas Martins"
        assert response.data[1]["colaborador"] == "Ana Oliveira"
