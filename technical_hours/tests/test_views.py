import datetime
from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)
from technical_hours.views import TechnicalHoursTableView

URL = "/api/horas-tecnicas/"


def test_technical_hours_table_returns_200():
    with patch.object(TechnicalHoursTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/horas-tecnicas/")
        assert response.status_code == 200


def test_technical_hours_table_returns_list(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get("/api/horas-tecnicas/")
        assert isinstance(response.data, list)
        assert len(response.data) == 1


def test_technical_hours_table_retorna_campos_corretos(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get("/api/horas-tecnicas/")

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


def test_technical_hours_table_lista_vazia_retorna_200():
    with patch.object(TechnicalHoursTableView, "get_queryset", return_value=[]):
        client = APIClient()
        response = client.get("/api/horas-tecnicas/")
        assert response.status_code == 200
        assert response.data == []


def test_technical_hours_table_retorna_multiplos_registros(tempo_em_memoria):
    now = timezone.now()

    programa = SilverPrograma(
        id=2,
        codigo_programa="PROG-002",
        nome_programa="Desenvolvimento",
        silver_ingested_at=now,
    )
    projeto = SilverProjeto(
        id=2,
        codigo_projeto="PROJ-002",
        nome_projeto="Portal Web",
        custo_hora=250.00,
        silver_ingested_at=now,
    )
    projeto.programa = programa

    tarefa2 = SilverTarefaProjeto(
        id=2,
        codigo_tarefa="TAR-002",
        titulo="Desenvolvimento",
        responsavel="Full Stack Dev",
        estimativa_horas=520,
        silver_ingested_at=now,
    )
    tarefa2.projeto = projeto

    tempo2 = SilverTempoTarefa(
        id=2,
        usuario="Ana Oliveira",
        data=datetime.date(2024, 1, 10),
        horas_trabalhadas=52.00,
        silver_ingested_at=now,
    )
    tempo2.tarefa = tarefa2
    tempo2.custo_por_hora = 250.00
    tempo2.custo_total = 52.00 * 250.00

    with patch.object(
        TechnicalHoursTableView,
        "get_queryset",
        return_value=[tempo_em_memoria, tempo2],
    ):
        client = APIClient()
        response = client.get("/api/horas-tecnicas/")
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["colaborador"] == "Lucas Martins"
        assert response.data[1]["colaborador"] == "Ana Oliveira"


# ─── Filtros por período ─────────────────────────────────────────────────────


def test_filtro_por_periodo_yyyy_mm_retorna_200(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get(f"{URL}?periodo=2024-03")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["periodo"] == "2024-03"


def test_filtro_por_ano_retorna_200(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get(f"{URL}?ano=2024")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_mes_retorna_200(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get(f"{URL}?mes=3")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_filtro_por_ano_e_mes_retorna_200(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get(f"{URL}?ano=2024&mes=3")
        assert response.status_code == 200
        assert len(response.data) == 1


def test_periodo_invalido_retorna_400():
    client = APIClient()
    response = client.get(f"{URL}?periodo=invalido")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_periodo_com_tres_partes_retorna_400():
    client = APIClient()
    response = client.get(f"{URL}?periodo=2024-03-15")
    assert response.status_code == 400
    assert "periodo" in response.data


def test_ano_nao_numerico_retorna_400():
    client = APIClient()
    response = client.get(f"{URL}?ano=abc")
    assert response.status_code == 400
    assert "ano" in response.data


def test_mes_nao_numerico_retorna_400():
    client = APIClient()
    response = client.get(f"{URL}?mes=abc")
    assert response.status_code == 400
    assert "mes" in response.data


def test_sem_filtro_retorna_todos_registros(tempo_em_memoria):
    with patch.object(
        TechnicalHoursTableView, "get_queryset", return_value=[tempo_em_memoria]
    ):
        client = APIClient()
        response = client.get(URL)
        assert response.status_code == 200
        assert len(response.data) == 1
