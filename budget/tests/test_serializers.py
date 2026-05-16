import datetime

from budget.serializers import BudgetProjectSerializer, GoldBudgetSnapshotSerializer
from sca_data.models import GoldBudgetSnapshot, SilverPrograma, SilverProjeto


def test_budget_project_serializer_returns_expected_fields():
    programa = SilverPrograma(nome_programa="Programa Alpha")
    projeto = SilverProjeto(
        id=1,
        nome_projeto="Projeto A",
        data_inicio=datetime.date(2026, 1, 10),
        status="Em andamento",
    )
    projeto.programa = programa
    projeto.budget = 1000
    projeto.custo_materiais = 200
    projeto.custo_horas = 300
    projeto.desvio_percent = 50
    projeto.saude_financeira = "Saudável"
    projeto.projecao_estouro = None

    data = BudgetProjectSerializer(projeto).data

    assert data["projeto"] == "Projeto A"
    assert data["programa"] == "Programa Alpha"
    assert data["budget"] == 1000
    assert data["custoMateriais"] == 200
    assert data["custoHoras"] == 300
    assert data["custoReal"] == 500
    assert data["desvioPercent"] == 50
    assert data["saude"] == "Saudável"
    assert data["periodo"] == "2026-01"


def test_gold_budget_snapshot_serializer_returns_expected_fields():
    row = GoldBudgetSnapshot(
        id=2,
        nome_projeto="Projeto Gold",
        nome_programa="Programa Beta",
        budget=8000.0,
        custo_materiais=3000.0,
        custo_horas=2500.0,
        custo_real=5500.0,
        desvio_percent=68.8,
        saude_financeira="Saudável",
        projecao_estouro=None,
        periodo="2026-03",
        status="Em andamento",
    )

    data = GoldBudgetSnapshotSerializer(row).data

    assert data["id"] == 2
    assert data["projeto"] == "Projeto Gold"
    assert data["programa"] == "Programa Beta"
    assert data["budget"] == 8000.0
    assert data["custoMateriais"] == 3000.0
    assert data["custoHoras"] == 2500.0
    assert data["custoReal"] == 5500.0
    assert data["desvioPercent"] == 68.8
    assert data["saude"] == "Saudável"
    assert data["projecaoEstouro"] is None
    assert data["periodo"] == "2026-03"
    assert data["status"] == "Em andamento"


def test_gold_budget_snapshot_serializer_sem_programa():
    row = GoldBudgetSnapshot(
        id=3,
        nome_projeto="Projeto Sem Programa",
        nome_programa=None,
        budget=0.0,
        custo_materiais=0.0,
        custo_horas=0.0,
        custo_real=0.0,
        desvio_percent=0.0,
        saude_financeira="Saudável",
        projecao_estouro=None,
        periodo="2026-01",
        status="Planejado",
    )

    data = GoldBudgetSnapshotSerializer(row).data

    assert data["programa"] == "Sem programa"


def test_gold_budget_snapshot_serializer_com_projecao_estouro():
    row = GoldBudgetSnapshot(
        id=4,
        nome_projeto="Projeto Crítico",
        nome_programa="Programa Gamma",
        budget=5000.0,
        custo_materiais=3000.0,
        custo_horas=3500.0,
        custo_real=6500.0,
        desvio_percent=130.0,
        saude_financeira="Crítico",
        projecao_estouro=1500.0,
        periodo="2026-02",
        status="Em andamento",
    )

    data = GoldBudgetSnapshotSerializer(row).data

    assert data["saude"] == "Crítico"
    assert data["projecaoEstouro"] == 1500.0
