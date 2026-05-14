import datetime
from unittest.mock import MagicMock, patch

from budget.selectors import get_budget_indicators, get_budget_indicators_gold


def _make_project_row(budget, custo_materiais, custo_horas, saude):
    p = MagicMock()
    p.budget = budget
    p.custo_materiais = custo_materiais
    p.custo_horas = custo_horas
    p.desvio_percent = round((custo_materiais + custo_horas) / budget * 100, 1) if budget else 0.0
    p.saude_financeira = saude
    return p


class TestGetBudgetIndicators:

    def test_returns_zeros_when_no_rows(self):
        with patch("budget.selectors.get_budget_snapshot", return_value=[]):
            result = get_budget_indicators({})

        assert result["budget_total"] == 0.0
        assert result["custo_real_total"] == 0.0
        assert result["desvio_percent_medio"] == 0.0
        assert result["projetos_saudaveis"] == 0
        assert result["projetos_atencao"] == 0
        assert result["projetos_criticos"] == 0

    def test_sums_budget_and_custo_real(self):
        rows = [
            _make_project_row(1000, 200, 300, "Saudável"),
            _make_project_row(2000, 800, 600, "Atenção"),
        ]
        with patch("budget.selectors.get_budget_snapshot", return_value=rows):
            result = get_budget_indicators({})

        assert result["budget_total"] == 3000.0
        assert result["custo_real_total"] == 1900.0

    def test_counts_by_saude(self):
        rows = [
            _make_project_row(1000, 400, 200, "Saudável"),
            _make_project_row(1000, 400, 300, "Saudável"),
            _make_project_row(1000, 600, 200, "Atenção"),
            _make_project_row(1000, 900, 100, "Crítico"),
        ]
        with patch("budget.selectors.get_budget_snapshot", return_value=rows):
            result = get_budget_indicators({})

        assert result["projetos_saudaveis"] == 2
        assert result["projetos_atencao"] == 1
        assert result["projetos_criticos"] == 1

    def test_calculates_desvio_percent_medio(self):
        rows = [
            _make_project_row(1000, 400, 200, "Saudável"),   # 60%
            _make_project_row(1000, 400, 400, "Atenção"),    # 80%
        ]
        with patch("budget.selectors.get_budget_snapshot", return_value=rows):
            result = get_budget_indicators({})

        assert result["desvio_percent_medio"] == 70.0

    def test_passes_params_to_snapshot(self):
        with patch(
            "budget.selectors.get_budget_snapshot", return_value=[]
        ) as mock_snap:
            get_budget_indicators({"programa": "Alpha", "periodo": "2026-01"})

        mock_snap.assert_called_once_with({"programa": "Alpha", "periodo": "2026-01"})


class TestGetBudgetIndicatorsGold:

    def _make_gold_qs(self, exists=True):
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        qs.exists.return_value = exists
        qs.aggregate.return_value = {
            "budget_total": 20000.0,
            "custo_real_total": 14000.0,
            "desvio_percent_medio": 68.5,
            "projetos_saudaveis": 4,
            "projetos_atencao": 2,
            "projetos_criticos": 1,
        }
        return qs

    def test_returns_none_when_gold_empty(self):
        empty_qs = self._make_gold_qs(exists=False)
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = empty_qs
            result = get_budget_indicators_gold({})

        assert result is None

    def test_returns_aggregate_when_gold_has_data(self):
        qs = self._make_gold_qs(exists=True)
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            result = get_budget_indicators_gold({})

        assert result is not None
        assert result["budget_total"] == 20000.0
        assert result["custo_real_total"] == 14000.0
        assert result["projetos_saudaveis"] == 4

    def test_filters_are_applied_before_aggregate(self):
        qs = self._make_gold_qs(exists=True)
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_indicators_gold({"programa": "Alpha"})

        qs.filter.assert_any_call(nome_programa__iexact="Alpha")
