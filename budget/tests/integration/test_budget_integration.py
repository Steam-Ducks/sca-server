"""
Conjunto de integração: Budget (Saúde Financeira)

Funções do conjunto:
    get_budget_snapshot_gold (selectors) — lê GoldBudgetSnapshot
    BudgetSnapshotView (views.py)        — GET /api/budget/
    GoldBudgetSnapshotSerializer         — renomeia campos do modelo:
        nome_projeto     → "projeto"
        saude_financeira → "saude"
        custo_materiais  → "custoMateriais"
        custo_horas      → "custoHoras"
        custo_real       → "custoReal"
        desvio_percent   → "desvioPercent"
        projecao_estouro → "projecaoEstouro"
"""

import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import GoldBudgetSnapshot


@pytest.fixture
def snapshot_gold(db):
    return GoldBudgetSnapshot.objects.create(
        id=600,
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

    NOTA: O serializer usa camelCase e renomeia campos do modelo.
    Campos retornados na resposta: projeto, programa, budget, custoMateriais,
    custoHoras, custoReal, desvioPercent, saude, projecaoEstouro, periodo, status.
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
        # FIX: serializer usa "projeto" (não "nome_projeto")
        assert projeto_data["projeto"] == "Conversor AC-DC"
        assert float(projeto_data["budget"]) == 500_000.0

    def test_saude_financeira_reflete_valor_do_banco(self, snapshot_gold):
        response = APIClient().get("/api/budget/")
        projeto_data = response.data["data"][0]
        # FIX: serializer usa "saude" (não "saude_financeira")
        assert projeto_data["saude"] == "Saudável"

    def test_last_updated_at_retorna_timestamp_da_gold(self, snapshot_gold):
        response = APIClient().get("/api/budget/")
        assert response.data["last_updated_at"] is not None

    def test_gold_vazia_retorna_lista_vazia_de_dados(self):
        response = APIClient().get("/api/budget/")
        assert response.status_code == 200
        assert isinstance(response.data["data"], list)

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
        # FIX: serializer usa "projeto" (não "nome_projeto")
        nomes = [p["projeto"] for p in response.data["data"]]
        assert "Proj MANSUP" in nomes
        assert "Proj INFRA" not in nomes
