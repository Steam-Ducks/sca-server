import datetime

from budget.serializers import BudgetProjectSerializer
from sca_data.models import SilverPrograma, SilverProjeto


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
