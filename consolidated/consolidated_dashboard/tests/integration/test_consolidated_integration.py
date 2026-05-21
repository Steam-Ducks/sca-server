"""
Conjunto de integração: Consolidated Dashboard

Funções do conjunto:
    SilverProjeto + relacionados (sca_data.models) — tabelas silver (PostgreSQL)
    ConsolidatedDashboardView (views.py)           — GET /api/consolidated/
    ConsolidatedDashboardPeriodoView               — GET /api/consolidated/periodo/<YYYY-MM>/
    ConsolidatedDashboardSerializer                — serializa campos consolidados
    URL: /api/consolidated/

Por que este conjunto existe:
    Os testes unitários usam fixtures em memória (sem banco).
    Este conjunto valida que a agregação real de custos de materiais
    e horas técnicas pelo ORM funciona com dados persistidos,
    exercitando a cadeia: banco silver → annotate/Sum → serializer → response.
"""

import os
import pytest
from datetime import date, datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import (
    SilverComprasProjeto,
    SilverPedidoCompra,
    SilverPrograma,
    SilverProjeto,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)

# Skip quando PostgreSQL não está disponível (CI SQLite).
# Para rodar localmente: export DB_HOST=postgres
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver schema — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        codigo_programa="MANSUP",
        nome_programa="MANSUP",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        codigo_projeto="PROJ-001",
        nome_projeto="Conversor DC-DC",
        programa=programa,
        custo_hora=300.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def compra(db, projeto):
    """Pedido de compra de R$ 50.000 em 2024-03."""
    pedido = SilverPedidoCompra.objects.create(
        data_pedido=date(2024, 3, 10),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    SilverComprasProjeto.objects.create(
        projeto=projeto,
        pedido_compra=pedido,
        valor_alocado=50_000.0,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    return pedido


@pytest.fixture
def horas(db, projeto):
    """10 horas técnicas a R$ 300/h = R$ 3.000 em 2024-03."""
    tarefa = SilverTarefaProjeto.objects.create(
        codigo_tarefa="TAR-001",
        titulo="Integração",
        projeto=projeto,
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    SilverTempoTarefa.objects.create(
        tarefa=tarefa,
        horas_trabalhadas=10.0,
        data=date(2024, 3, 15),
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )
    return tarefa


class TestConsolidatedDashboardIntegration:
    """
    CTI-01 ao CTI-05
    Conjunto: SilverProjeto + ConsolidatedDashboardView + ConsolidatedDashboardSerializer

    Carga: 0–2 objetos por camada silver (programa → projeto → compra/horas).
    """

    def test_lista_retorna_200(self):
        # CTI-01 (mínimo): banco vazio → GET /api/consolidated/ retorna 200
        # Valida: rota registrada, view responde sem dados silver
        response = APIClient().get("/api/consolidated/")
        assert response.status_code == 200

    def test_lista_vazia_com_banco_vazio(self):
        # CTI-02 (mínimo): sem projetos no banco → resposta com data vazia
        # Valida: view não lança exceção com silver vazio
        response = APIClient().get("/api/consolidated/")
        assert response.status_code == 200
        assert "data" in response.data
        assert isinstance(response.data["data"], list)

    def test_custo_materiais_agregado_pelo_orm(self, projeto, compra):
        # CTI-03 (mínimo): compra real no banco → custo_materiais somado na resposta
        # Valida: annotate(Sum) em SilverComprasProjeto → serializer → response
        response = APIClient().get("/api/consolidated/")

        assert response.status_code == 200
        rows = response.data["data"]
        assert len(rows) == 1
        assert rows[0]["nome_projeto"] == "Conversor DC-DC"
        assert float(rows[0]["custo_materiais"]) == 50_000.0

    def test_custo_horas_agregado_pelo_orm(self, projeto, horas):
        # CTI-04 (mínimo): horas técnicas reais → custo_horas = horas × custo_hora
        # Valida: annotate(Sum(horas * custo_hora)) em SilverTempoTarefa → response
        response = APIClient().get("/api/consolidated/")

        rows = response.data["data"]
        assert len(rows) == 1
        # 10h × R$ 300/h = R$ 3.000
        assert float(rows[0]["custo_horas"]) == 3_000.0

    def test_filtro_por_programa(self, projeto, compra):
        # CTI-05 (mínimo): ?programa= → response contém só projetos do programa
        # Valida: filter(programa__nome_programa=) aplicado antes da agregação
        response = APIClient().get("/api/consolidated/?programa=MANSUP")

        assert response.status_code == 200
        nomes = [r["nome_projeto"] for r in response.data["data"]]
        assert "Conversor DC-DC" in nomes

        # Programa inexistente → lista vazia
        response2 = APIClient().get("/api/consolidated/?programa=INEXISTENTE")
        assert response2.data["data"] == []


class TestConsolidatedPeriodoIntegration:
    """
    CTI-06 ao CTI-08
    Conjunto: ConsolidatedDashboardPeriodoView — rota /api/consolidated/periodo/<YYYY-MM>/

    Carga: 0–2 objetos silver com datas em meses distintos.
    """

    def test_periodo_valido_retorna_200(self):
        # CTI-06 (mínimo): período válido no path → 200
        # Valida: _parse_periodo converte YYYY-MM → intervalo de datas aceito pelo ORM
        response = APIClient().get("/api/consolidated/periodo/2024-03/")
        assert response.status_code == 200

    def test_periodo_invalido_retorna_400(self):
        # CTI-07 (adicional): formato inválido → 400 ValidationError
        # Valida: _parse_periodo levanta DRFValidationError propagada pela view
        response = APIClient().get("/api/consolidated/periodo/2024-13/")
        assert response.status_code == 400

    def test_periodo_filtra_apenas_dados_do_mes(self, projeto, compra):
        # CTI-08 (mínimo): compra em 2024-03 → período 2024-02 não retorna
        # Valida: intervalo data_inicio/data_fim aplicado ao queryset
        response_correto = APIClient().get("/api/consolidated/periodo/2024-03/")
        response_errado = APIClient().get("/api/consolidated/periodo/2024-02/")

        assert response_correto.status_code == 200
        assert response_errado.status_code == 200
        assert len(response_correto.data["data"]) == 1
        assert len(response_errado.data["data"]) == 0
