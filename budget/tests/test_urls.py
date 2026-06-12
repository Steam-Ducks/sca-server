from django.urls import resolve

from budget.views import BudgetIndicatorsView, BudgetSnapshotView


def test_budget_route_resolves():
    match = resolve("/api/budget/")
    assert match.func.view_class == BudgetSnapshotView


def test_budget_indicators_route_resolves():
    match = resolve("/api/budget/indicators/")
    assert match.func.view_class == BudgetIndicatorsView
