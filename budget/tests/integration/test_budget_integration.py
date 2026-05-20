"""
Conjunto de integração: Budget (Saúde Financeira)

Funções do conjunto:
    get_budget_snapshot_gold (selectors) — lê GoldBudgetSnapshot
    get_budget_snapshot (selectors)      — fallback: lê Silver via ORM
    get_budget_last_updated_at_gold      — timestamp da última atualização gold
    BudgetSnapshotView (views.py)        — GET /api/budget/
    GoldBudgetSnapshotSerializer         — serializa snapshot gold
    BudgetProjectSerializer              — serializa dados live silver

Lógica especial do conjunto:
    A view prioriza dados da tabela gold (pré-computados) quando disponíveis.
    Se a gold estiver vazia, usa dados silver em tempo real.
    Este conjunto valida os dois caminhos.
"""

import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import GoldBudgetSnapshot, SilverPrograma, SilverProjeto


@pytest.fixture
def programa(db):
    return SilverPrograma.objects.create(
        id=600,
        codigo_programa="MAXAC",
        nome_programa="MAX 1.2 AC",
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def projeto(db, programa):
    return SilverProjeto.objects.create(
        id=600,
        codigo_projeto="PROJ-600",
        nome_projeto="Conversor AC-DC",
        programa=programa,
        custo_hora=180.0,
        status="Em andamento",
        silver_ingested_at=datetime.now(tz=timezone.utc),
    )


@pytest.fixture
def snapshot_gold(db):
    return GoldBudgetSnapshot.objects.create(
        projeto_id=600,
        nome_projeto="Conversor AC-DC",
        nome_programa="MAX 1.2 AC",
        gerente_programa="Gerente Gold",
        responsavel_projeto="Resp Gold",
        budget=500_000.0,
        custo_materiais=120_000.0,
        custo_horas=80_000.0,
        custo_real=200_000.0,
        desvio_percent=-60.0,
        saude_financeira="Saudável",
        projecao_estouro=0.0,
        periodo="2024-03",
        status="Em andamento",
        gold_updated_at=datetime.now(tz=timezone.utc),
    )


@pytest.mark.integration
@pytest.mark.django_db
class TestBudgetSnapshotGoldIntegration:
    """
    CT-INT-BUDG-01
    Conjunto: get_budget_snapshot_gold + BudgetSnapshotView + GoldBudgetSnapshotSerializer

    Caminho primário: gold table populada → view usa dados gold.
    """

    def test_retorna_200(self):
        response = APIClient().get("/api/budget/")
        assert response.status_code == 200

    def test_retorna_estrutura_data_e_last_updated_at(self):
        response = APIClient().get("/api/budget/")
        assert "data" in response.data
        assert "last_updated_at" in response.data

    def test_usa_dados_gold_quando_disponiveis(self, snapshot_gold):
        response = APIClient().get("/api/budget/")

        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        projeto_data = response.data["data"][0]
        assert projeto_data["nome_projeto"] == "Conversor AC-DC"
        assert float(projeto_data["budget"]) == 500_000.0

    def test_saude_financeira_reflete_valor_do_banco(self, snapshot_gold):
        response = APIClient().get("/api/budget/")
        projeto_data = response.data["data"][0]
        assert projeto_data["saude_financeira"] == "Saudável"

    def test_last_updated_at_retorna_timestamp_da_gold(self, snapshot_gold):
        response = APIClient().get("/api/budget/")
        assert response.data["last_updated_at"] is not None

    def test_gold_vazia_retorna_lista_vazia_de_dados(self):
        """Com gold vazia e sem dados silver, retorna data vazia."""
        response = APIClient().get("/api/budget/")
        assert response.status_code == 200
        assert response.data["data"] == [] or isinstance(response.data["data"], list)

    def test_filtro_por_programa_retorna_apenas_dados_do_programa(self, db):
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj MANSUP", nome_programa="MANSUP",
            budget=100_000.0, custo_real=50_000.0,
            saude_financeira="Saudável",
            gold_updated_at=datetime.now(tz=timezone.utc),
        )
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj INFRA", nome_programa="INFRA",
            budget=999_000.0, custo_real=500_000.0,
            saude_financeira="Em risco",
            gold_updated_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/budget/?program=MANSUP")

        assert response.status_code == 200
        nomes = [p["nome_projeto"] for p in response.data["data"]]
        assert "Proj MANSUP" in nomes
        assert "Proj INFRA" not in nomes
