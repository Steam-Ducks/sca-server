import datetime
from unittest.mock import MagicMock, patch

from budget.selectors import (
    _apply_project_filters,
    get_budget_last_updated_at_gold,
    get_budget_snapshot,
    get_budget_snapshot_gold,
)


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


class TestApplyProjectFilters:
    """CT06 — filtro de projeto restrito ao programa; silver path."""

    def _qs(self):
        qs = MagicMock()
        qs.filter.return_value = qs
        return qs

    def test_filters_by_programa(self):
        qs = self._qs()
        _apply_project_filters(qs, {"programa": "Alpha"})
        qs.filter.assert_called_with(programa__nome_programa__iexact="Alpha")

    def test_filters_by_projeto(self):
        qs = self._qs()
        _apply_project_filters(qs, {"projeto": "Projeto A"})
        qs.filter.assert_called_with(nome_projeto__iexact="Projeto A")

    def test_filters_by_status(self):
        qs = self._qs()
        _apply_project_filters(qs, {"status": "Em andamento"})
        qs.filter.assert_called_with(status__iexact="Em andamento")

    def test_filters_by_periodo(self):
        qs = self._qs()
        _apply_project_filters(qs, {"periodo": "2026-01"})
        qs.filter.assert_called_with(data_inicio__year=2026, data_inicio__month=1)

    def test_no_filter_when_empty_params(self):
        qs = self._qs()
        result = _apply_project_filters(qs, {})
        qs.filter.assert_not_called()
        assert result is qs

    def test_combined_programa_and_projeto_filters(self):
        qs = self._qs()
        _apply_project_filters(qs, {"programa": "Beta", "projeto": "Projeto B"})
        calls = [str(c) for c in qs.filter.call_args_list]
        assert any("Beta" in c for c in calls)
        assert any("Projeto B" in c for c in calls)


class TestGetBudgetSnapshotSaudeFilter:
    """CT04 — filtro de saúde financeira aplicado client-side no caminho silver."""

    def _make_projeto(self, saude, budget=1000):
        p = MagicMock()
        p.budget_materiais = budget
        p.budget_horas = 0
        p.custo_materiais = budget * 0.5
        p.custo_horas = 0
        p.nome_projeto = f"Proj {saude}"
        p.saude_financeira = saude
        return p

    def _mock_qs(self, fake_rows):
        qs = MagicMock()
        qs.order_by.return_value = fake_rows
        return qs

    def test_saude_filter_keeps_only_matching_rows(self):
        """Quando saude='Saudável', apenas projetos saudáveis permanecem."""
        fake_rows = [
            self._make_projeto("Saudável", 1000),
            self._make_projeto("Atenção", 1000),
            self._make_projeto("Crítico", 1000),
        ]

        with patch(
            "budget.selectors._apply_project_filters",
            return_value=self._mock_qs(fake_rows),
        ):
            with patch(
                "budget.selectors._build_date_filters",
                return_value=(MagicMock(), MagicMock()),
            ):
                with patch("budget.selectors._sum_subquery", return_value=MagicMock()):
                    with patch("budget.selectors.SilverProjeto") as mock_model:
                        mock_model.objects.select_related.return_value.annotate.return_value = (
                            MagicMock()
                        )
                        rows = get_budget_snapshot({"saude": "Saudável"})

        assert all(r.saude_financeira == "Saudável" for r in rows)

    def test_no_saude_filter_returns_all_rows(self):
        fake_rows = [
            self._make_projeto("Saudável", 1000),
            self._make_projeto("Atenção", 1000),
        ]

        with patch(
            "budget.selectors._apply_project_filters",
            return_value=self._mock_qs(fake_rows),
        ):
            with patch(
                "budget.selectors._build_date_filters",
                return_value=(MagicMock(), MagicMock()),
            ):
                with patch("budget.selectors._sum_subquery", return_value=MagicMock()):
                    with patch("budget.selectors.SilverProjeto") as mock_model:
                        mock_model.objects.select_related.return_value.annotate.return_value = (
                            MagicMock()
                        )
                        rows = get_budget_snapshot({})

        assert len(rows) == 2


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
