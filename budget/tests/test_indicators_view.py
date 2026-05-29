import datetime
from unittest.mock import MagicMock, patch

from rest_framework.test import APIClient


def _auth_client():
    user = MagicMock()
    user.usuario_perfil.perfil.permissoes = "super_admin"
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _indicators_gold():
    return {
        "budget_total": 15000.0,
        "custo_real_total": 10500.0,
        "desvio_percent_medio": 65.3,
        "projetos_saudaveis": 3,
        "projetos_atencao": 2,
        "projetos_criticos": 1,
    }


def _indicators_silver():
    return {
        "budget_total": 8000.0,
        "custo_real_total": 5000.0,
        "desvio_percent_medio": 50.0,
        "projetos_saudaveis": 2,
        "projetos_atencao": 1,
        "projetos_criticos": 0,
    }


class TestBudgetIndicatorsReturns200:

    def test_returns_200_with_gold_data(self):
        updated_at = datetime.datetime(2026, 5, 1, 12, 0, tzinfo=datetime.timezone.utc)

        with patch(
            "budget.views.get_budget_indicators_gold", return_value=_indicators_gold()
        ):
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=updated_at
            ):
                response = _auth_client().get("/api/budget/indicators/")

        assert response.status_code == 200

    def test_returns_200_with_silver_fallback(self):
        with patch("budget.views.get_budget_indicators_gold", return_value=None):
            with patch(
                "budget.views.get_budget_indicators", return_value=_indicators_silver()
            ):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    response = _auth_client().get("/api/budget/indicators/")

        assert response.status_code == 200


class TestBudgetIndicatorsResponseShape:

    def test_gold_response_contains_all_fields(self):
        updated_at = datetime.datetime(2026, 5, 1, 10, 0, tzinfo=datetime.timezone.utc)

        with patch(
            "budget.views.get_budget_indicators_gold", return_value=_indicators_gold()
        ):
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=updated_at
            ):
                response = _auth_client().get("/api/budget/indicators/")

        data = response.data["data"]
        assert data["budgetTotal"] == 15000.0
        assert data["custoRealTotal"] == 10500.0
        assert data["desvioPercentMedio"] == 65.3
        assert data["projetosSaudaveis"] == 3
        assert data["projetosAtencao"] == 2
        assert data["projetosCriticos"] == 1
        assert response.data["last_updated_at"] == "2026-05-01T10:00:00+00:00"

    def test_silver_fallback_response_contains_all_fields(self):
        updated_at = datetime.datetime(2026, 4, 20, 8, 0, tzinfo=datetime.timezone.utc)

        with patch("budget.views.get_budget_indicators_gold", return_value=None):
            with patch(
                "budget.views.get_budget_indicators", return_value=_indicators_silver()
            ):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=updated_at
                ):
                    response = _auth_client().get("/api/budget/indicators/")

        data = response.data["data"]
        assert data["budgetTotal"] == 8000.0
        assert data["custoRealTotal"] == 5000.0
        assert data["projetosSaudaveis"] == 2
        assert data["projetosAtencao"] == 1
        assert data["projetosCriticos"] == 0
        assert response.data["last_updated_at"] == "2026-04-20T08:00:00+00:00"

    def test_last_updated_at_is_none_when_no_data(self):
        empty = {
            "budget_total": 0.0,
            "custo_real_total": 0.0,
            "desvio_percent_medio": 0.0,
            "projetos_saudaveis": 0,
            "projetos_atencao": 0,
            "projetos_criticos": 0,
        }

        with patch("budget.views.get_budget_indicators_gold", return_value=None):
            with patch("budget.views.get_budget_indicators", return_value=empty):
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    response = _auth_client().get("/api/budget/indicators/")

        assert response.data["last_updated_at"] is None
        assert response.data["data"]["budgetTotal"] == 0.0


class TestBudgetIndicatorsGoldPriority:

    def test_gold_takes_priority_over_silver(self):
        with patch(
            "budget.views.get_budget_indicators_gold", return_value=_indicators_gold()
        ):
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=None
            ):
                with patch("budget.views.get_budget_indicators") as mock_silver:
                    response = _auth_client().get("/api/budget/indicators/")

        assert response.status_code == 200
        mock_silver.assert_not_called()

    def test_falls_back_to_silver_when_gold_returns_none(self):
        with patch("budget.views.get_budget_indicators_gold", return_value=None):
            with patch(
                "budget.views.get_budget_indicators", return_value=_indicators_silver()
            ) as mock_silver:
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    response = _auth_client().get("/api/budget/indicators/")

        assert response.status_code == 200
        mock_silver.assert_called_once()


class TestBudgetIndicatorsFilters:

    def test_query_params_are_passed_to_gold_selector(self):
        with patch(
            "budget.views.get_budget_indicators_gold", return_value=_indicators_gold()
        ) as mock_gold:
            with patch(
                "budget.views.get_budget_last_updated_at_gold", return_value=None
            ):
                _auth_client().get(
                    "/api/budget/indicators/?programa=Alpha&projeto=P1&periodo=2026-01"
                )

        call_params = mock_gold.call_args[0][0]
        assert call_params.get("programa") == "Alpha"
        assert call_params.get("projeto") == "P1"
        assert call_params.get("periodo") == "2026-01"

    def test_query_params_are_passed_to_silver_selector(self):
        with patch("budget.views.get_budget_indicators_gold", return_value=None):
            with patch(
                "budget.views.get_budget_indicators",
                return_value=_indicators_silver(),
            ) as mock_silver:
                with patch(
                    "budget.views.get_budget_last_updated_at", return_value=None
                ):
                    _auth_client().get(
                        "/api/budget/indicators/?saude=Saud%C3%A1vel&periodo=2026-02"
                    )

        call_params = mock_silver.call_args[0][0]
        assert call_params.get("saude") == "Saudável"
        assert call_params.get("periodo") == "2026-02"
