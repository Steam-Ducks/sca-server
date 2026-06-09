"""
Conjunto de integração: Budget (Saúde Financeira)

Funções do conjunto:
    get_budget_snapshot_gold (selectors) — lê GoldBudgetSnapshot
    get_budget_indicators_gold           — agrega KPIs do gold
    BudgetSnapshotView    GET /api/budget/
    BudgetIndicatorsView  GET /api/budget/indicators/   ← NOVO
    GoldBudgetSnapshotSerializer  — renomeia campos do modelo
    BudgetIndicatorsSerializer    — KPIs agregados em camelCase
"""

import os
import pytest
from datetime import datetime, timezone

from sca_data.models import GoldBudgetSnapshot

pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("DB_HOST"),
        reason="Requires PostgreSQL with silver/gold schemas — set DB_HOST to run",
    ),
    pytest.mark.integration,
    pytest.mark.django_db,
]


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


# ── CTI: BudgetSnapshotView ───────────────────────────────────────────────────

class TestBudgetSnapshotGoldIntegration:
    """
    CTI-01 ao CTI-07
    Conjunto: get_budget_snapshot_gold + BudgetSnapshotView + GoldBudgetSnapshotSerializer

    Carga: 0–2 objetos GoldBudgetSnapshot por teste.
    Campos retornados: projeto, programa, budget, custoMateriais,
    custoHoras, custoReal, desvioPercent, saude, projecaoEstouro, periodo, status.
    """

    def test_retorna_200(self, api_client):
        # CTI-01 (mínimo): banco vazio → 200
        response = api_client.get("/api/budget/")
        assert response.status_code == 200

    def test_retorna_estrutura_data_e_last_updated_at(self, api_client):
        # CTI-02 (mínimo): envelope {"data": [...], "last_updated_at": ...}
        response = api_client.get("/api/budget/")
        assert "data" in response.data
        assert "last_updated_at" in response.data

    def test_usa_dados_gold_quando_disponiveis(self, api_client, snapshot_gold):
        # CTI-03 (mínimo): dado gold → aparece na resposta com campos corretos
        response = api_client.get("/api/budget/")
        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        item = response.data["data"][0]
        assert item["projeto"] == "Conversor AC-DC"
        assert float(item["budget"]) == 500_000.0

    def test_saude_financeira_reflete_valor_do_banco(self, api_client, snapshot_gold):
        # CTI-04 (adicional): saude_financeira → "saude" (camelCase)
        response = api_client.get("/api/budget/")
        assert response.data["data"][0]["saude"] == "Saudável"

    def test_last_updated_at_retorna_timestamp_da_gold(self, api_client, snapshot_gold):
        # CTI-05 (adicional): gold_updated_at → last_updated_at
        response = api_client.get("/api/budget/")
        assert response.data["last_updated_at"] is not None

    def test_gold_vazia_retorna_lista_vazia_de_dados(self, api_client):
        # CTI-06 (adicional): banco vazio → data é lista vazia
        response = api_client.get("/api/budget/")
        assert response.status_code == 200
        assert isinstance(response.data["data"], list)

    def test_filtro_por_programa_retorna_apenas_dados_do_programa(self, api_client, db):
        # CTI-07 (mínimo): ?programa= → isola dados do programa
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj MANSUP", nome_programa="MANSUP",
            budget=100_000.0, custo_real=50_000.0,
            saude_financeira="Saudável", gold_updated_at=datetime.now(tz=timezone.utc),
        )
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj INFRA", nome_programa="INFRA",
            budget=999_000.0, custo_real=500_000.0,
            saude_financeira="Em risco", gold_updated_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/budget/?programa=MANSUP")
        assert response.status_code == 200
        nomes = [p["projeto"] for p in response.data["data"]]
        assert "Proj MANSUP" in nomes
        assert "Proj INFRA" not in nomes


# ── CTI: BudgetIndicatorsView ─────────────────────────────────────────────────

class TestBudgetIndicatorsIntegration:
    """
    CTI-08 ao CTI-11
    Conjunto: get_budget_indicators_gold + BudgetIndicatorsView + BudgetIndicatorsSerializer
    GET /api/budget/indicators/

    Carga: 0–3 objetos GoldBudgetSnapshot por teste.
    Campos retornados (camelCase):
        budgetTotal, custoRealTotal, desvioPercentMedio,
        projetosSaudaveis, projetosAtencao, projetosCriticos
    """

    def test_indicators_retorna_200(self, api_client):
        # CTI-08 (mínimo): banco vazio → GET /api/budget/indicators/ retorna 200
        # Valida: rota registrada, view instanciada sem erro
        response = api_client.get("/api/budget/indicators/")
        assert response.status_code == 200

    def test_indicators_estrutura_data_e_last_updated_at(self, api_client):
        # CTI-09 (mínimo): envelope {"data": {...}, "last_updated_at": ...}
        # Valida: BudgetIndicatorsSerializer retorna objeto (não lista)
        response = api_client.get("/api/budget/indicators/")
        assert "data" in response.data
        assert "last_updated_at" in response.data

    def test_indicators_contem_campos_do_serializer(self, api_client):
        # CTI-10 (mínimo): todos os campos do BudgetIndicatorsSerializer presentes
        # Valida: camelCase correto e source fields mapeados
        response = api_client.get("/api/budget/indicators/")
        data = response.data["data"]
        for campo in ["budgetTotal", "custoRealTotal", "desvioPercentMedio",
                      "projetosSaudaveis", "projetosAtencao", "projetosCriticos"]:
            assert campo in data, f"Campo ausente: {campo}"

    def test_indicators_refletem_dados_reais(self, api_client, db):
        # CTI-11 (mínimo): dados inseridos → KPIs calculados corretamente
        # Valida: get_budget_indicators_gold agrega pelo banco real
        GoldBudgetSnapshot.objects.create(
            id=601, nome_projeto="Proj A", nome_programa="MANSUP",
            budget=200_000.0, custo_real=150_000.0, desvio_percent=25.0,
            saude_financeira="Saudável", gold_updated_at=datetime.now(tz=timezone.utc),
        )
        GoldBudgetSnapshot.objects.create(
            id=602, nome_projeto="Proj B", nome_programa="MANSUP",
            budget=100_000.0, custo_real=130_000.0, desvio_percent=-30.0,
            saude_financeira="Crítico", gold_updated_at=datetime.now(tz=timezone.utc),
        )
        response = api_client.get("/api/budget/indicators/")
        assert response.status_code == 200
        data = response.data["data"]
        # 2 projetos inseridos; totais devem refletir ambos
        assert float(data["budgetTotal"]) == 300_000.0
        assert int(data["projetosSaudaveis"]) == 1
        assert int(data["projetosCriticos"]) == 1
