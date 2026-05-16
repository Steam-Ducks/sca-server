import datetime
from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient

from sca_data.models import GoldBudgetSnapshot, SilverPrograma, SilverProjeto


def _make_silver_project():
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


def _make_gold_row():
    return GoldBudgetSnapshot(
        id=10,
        nome_projeto="Projeto Gold",
        nome_programa="Programa Gold",
        budget=5000.0,
        custo_materiais=2000.0,
        custo_horas=1500.0,
        custo_real=3500.0,
        desvio_percent=70.0,
        saude_financeira="Atenção",
        projecao_estouro=None,
        periodo="2026-01",
        status="Em andamento",
    )


def _empty_gold_qs():
    qs = MagicMock()
    qs.exists.return_value = False
    return qs


def _gold_qs_with(row):
    qs = MagicMock()
    qs.exists.return_value = True
    qs.__iter__ = MagicMock(return_value=iter([row]))
    return qs


class TestBudgetSnapshotReturns200:

    def test_returns_200_with_empty_data(self):
        with patch(
            "budget.views.get_budget_snapshot_gold", return_value=_empty_gold_qs()
        ):
            with patch("budget.views.get_budget_snapshot", return_value=[]):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    response = APIClient().get("/api/budget/")

        assert response.status_code == 200

    def test_returns_200_with_silver_fallback(self):
        projeto = _make_silver_project()
        updated_at = datetime.datetime(
            2026, 4, 26, 12, 30, tzinfo=datetime.timezone.utc
        )

        with patch(
            "budget.views.get_budget_snapshot_gold", return_value=_empty_gold_qs()
        ):
            with patch("budget.views.get_budget_snapshot", return_value=[projeto]):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=updated_at
                ):
                    response = APIClient().get("/api/budget/")

        assert response.status_code == 200
        assert response.data["last_updated_at"] == "2026-04-26T12:30:00+00:00"
        assert response.data["data"][0]["projeto"] == "Projeto A"
        assert response.data["data"][0]["desvioPercent"] == 50
        assert response.data["data"][0]["saude"] == "Saudável"

    def test_uses_gold_when_available(self):
        gold_row = _make_gold_row()
        updated_at = datetime.datetime(2026, 4, 27, 8, 0, tzinfo=datetime.timezone.utc)

        with patch(
            "budget.views.get_budget_snapshot_gold",
            return_value=_gold_qs_with(gold_row),
        ):
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=updated_at
            ):
                response = APIClient().get("/api/budget/")

        assert response.status_code == 200
        assert response.data["data"][0]["projeto"] == "Projeto Gold"
        assert response.data["data"][0]["saude"] == "Atenção"
        assert response.data["last_updated_at"] == "2026-04-27T08:00:00+00:00"

    def test_gold_takes_priority_over_silver(self):
        gold_row = _make_gold_row()

        with patch(
            "budget.views.get_budget_snapshot_gold",
            return_value=_gold_qs_with(gold_row),
        ):
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=None
            ):
                with patch("budget.views.get_budget_snapshot") as mock_silver:
                    response = APIClient().get("/api/budget/")

        assert response.status_code == 200
        mock_silver.assert_not_called()

    def test_last_updated_at_is_none_when_no_data(self):
        with patch(
            "budget.views.get_budget_snapshot_gold", return_value=_empty_gold_qs()
        ):
            with patch("budget.views.get_budget_snapshot", return_value=[]):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    response = APIClient().get("/api/budget/")

        assert response.data["last_updated_at"] is None
