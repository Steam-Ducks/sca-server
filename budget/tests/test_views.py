import datetime
from unittest.mock import patch

from rest_framework.test import APIClient

from budget.views import BudgetSnapshotView
from sca_data.models import SilverPrograma, SilverProjeto


def _make_project():
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
    return projeto


def test_budget_snapshot_returns_200():
    with patch.object(BudgetSnapshotView, "get", wraps=BudgetSnapshotView().get):
        with patch("budget.views.get_budget_snapshot", return_value=[]):
            with patch("budget.views.get_budget_last_updated_at", return_value=None):
                response = APIClient().get("/api/budget/")
                assert response.status_code == 200


def test_budget_snapshot_returns_payload():
    projeto = _make_project()
    updated_at = datetime.datetime(2026, 4, 26, 12, 30, tzinfo=datetime.timezone.utc)

    with patch("budget.views.get_budget_snapshot", return_value=[projeto]):
        with patch("budget.views.get_budget_last_updated_at", return_value=updated_at):
            response = APIClient().get("/api/budget/")

    assert response.status_code == 200
    assert response.data["last_updated_at"] == "2026-04-26T12:30:00+00:00"
    assert response.data["data"][0]["projeto"] == "Projeto A"
    assert response.data["data"][0]["desvioPercent"] == 50
    assert response.data["data"][0]["saude"] == "Saudável"
