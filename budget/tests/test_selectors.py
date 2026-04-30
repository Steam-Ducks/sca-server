import datetime
from unittest.mock import MagicMock, patch

from budget.selectors import get_budget_last_updated_at_gold, get_budget_snapshot_gold


def _make_gold_qs():
    qs = MagicMock()
    qs.filter.return_value = qs
    qs.order_by.return_value = qs
    return qs


class TestGetBudgetSnapshotGold:

    def test_returns_all_ordered_when_no_filters(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            result = get_budget_snapshot_gold({})

        mock_model.objects.all.assert_called_once()
        qs.order_by.assert_called_once_with("nome_projeto")
        assert result == qs

    def test_filters_by_programa(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"programa": "Alpha"})

        qs.filter.assert_any_call(nome_programa__iexact="Alpha")

    def test_filters_by_projeto(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"projeto": "Projeto A"})

        qs.filter.assert_any_call(nome_projeto__iexact="Projeto A")

    def test_filters_by_status(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"status": "Em andamento"})

        qs.filter.assert_any_call(status__iexact="Em andamento")

    def test_filters_by_periodo(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"periodo": "2026-01"})

        qs.filter.assert_any_call(periodo="2026-01")

    def test_filters_by_saude(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"saude": "Crítico"})

        qs.filter.assert_any_call(saude_financeira__iexact="Crítico")

    def test_ignores_empty_filter_values(self):
        qs = _make_gold_qs()
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.all.return_value = qs
            get_budget_snapshot_gold({"programa": "", "projeto": ""})

        qs.filter.assert_not_called()


class TestGetBudgetLastUpdatedAtGold:

    def test_returns_max_gold_updated_at(self):
        expected = datetime.datetime(2026, 4, 26, 12, 0, tzinfo=datetime.timezone.utc)
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.aggregate.return_value = {"latest": expected}
            result = get_budget_last_updated_at_gold()

        assert result == expected

    def test_returns_none_when_table_is_empty(self):
        with patch("budget.selectors.GoldBudgetSnapshot") as mock_model:
            mock_model.objects.aggregate.return_value = {"latest": None}
            result = get_budget_last_updated_at_gold()

        assert result is None
