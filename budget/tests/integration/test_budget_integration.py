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

import os
import pytest
from datetime import datetime, timezone
from rest_framework.test import APIClient

from sca_data.models import GoldBudgetSnapshot

# Skip when PostgreSQL is unavailable (SQLite CI environment).
# To run locally: export DB_HOST=postgres (or your host) before pytest.
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


class TestBudgetSnapshotGoldIntegration:
    """
    CTI-01 ao CTI-07
    Conjunto: get_budget_snapshot_gold + BudgetSnapshotView + GoldBudgetSnapshotSerializer

    Carga: 0–2 objetos GoldBudgetSnapshot por teste (banco limpo a cada teste).
    NOTA: O serializer usa camelCase e renomeia campos do modelo.
    Campos retornados: projeto, programa, budget, custoMateriais,
    custoHoras, custoReal, desvioPercent, saude, projecaoEstouro, periodo, status.
    """

    def test_retorna_200(self):
        # CTI-01 (mínimo): banco vazio → GET retorna 200
        # Valida: rota /api/budget/ registrada e view responde sem dados
        response = APIClient().get("/api/budget/")
        assert response.status_code == 200

    def test_retorna_estrutura_data_e_last_updated_at(self):
        # CTI-02 (mínimo): estrutura do envelope de resposta
        # Valida: serializer retorna {"data": [...], "last_updated_at": ...}
        response = APIClient().get("/api/budget/")
        assert "data" in response.data
        assert "last_updated_at" in response.data

    def test_usa_dados_gold_quando_disponiveis(self, snapshot_gold):
        # CTI-03 (mínimo): dado inserido na gold → aparece na resposta
        # Valida: selector lê GoldBudgetSnapshot → view → serializer → response
        response = APIClient().get("/api/budget/")

        assert response.status_code == 200
        assert len(response.data["data"]) == 1
        projeto_data = response.data["data"][0]
        assert projeto_data["projeto"] == "Conversor AC-DC"
        assert float(projeto_data["budget"]) == 500_000.0

    def test_saude_financeira_reflete_valor_do_banco(self, snapshot_gold):
        # CTI-04 (adicional): campo renomeado pelo serializer
        # Valida: saude_financeira (modelo) → "saude" (resposta camelCase)
        response = APIClient().get("/api/budget/")
        projeto_data = response.data["data"][0]
        assert projeto_data["saude"] == "Saudável"

    def test_last_updated_at_retorna_timestamp_da_gold(self, snapshot_gold):
        # CTI-05 (adicional): metadado de atualização
        # Valida: gold_updated_at do banco chega como last_updated_at na resposta
        response = APIClient().get("/api/budget/")
        assert response.data["last_updated_at"] is not None

    def test_gold_vazia_retorna_lista_vazia_de_dados(self):
        # CTI-06 (adicional): banco vazio → data é lista vazia, não null/erro
        # Valida: robustez da view quando gold não tem registros
        response = APIClient().get("/api/budget/")
        assert response.status_code == 200
        assert isinstance(response.data["data"], list)

    def test_filtro_por_programa_retorna_apenas_dados_do_programa(self, db):
        # CTI-07 (mínimo): filtro ?program= → isola dados do programa
        # Valida: filtro passado via query param → selector aplica WHERE → response filtrado
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj MANSUP",
            nome_programa="MANSUP",
            budget=100_000.0,
            custo_real=50_000.0,
            saude_financeira="Saudável",
            gold_updated_at=datetime.now(tz=timezone.utc),
        )
        GoldBudgetSnapshot.objects.create(
            nome_projeto="Proj INFRA",
            nome_programa="INFRA",
            budget=999_000.0,
            custo_real=500_000.0,
            saude_financeira="Em risco",
            gold_updated_at=datetime.now(tz=timezone.utc),
        )

        response = APIClient().get("/api/budget/?programa=MANSUP")
        assert response.status_code == 200
        # FIX: serializer usa "projeto" (não "nome_projeto")
        nomes = [p["projeto"] for p in response.data["data"]]
        assert "Proj MANSUP" in nomes
        assert "Proj INFRA" not in nomes
