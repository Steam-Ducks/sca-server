from django.urls import resolve

from budget.views import BudgetSnapshotView


def test_budget_route_resolves():
    match = resolve("/api/budget/")
    assert match.func.view_class == BudgetSnapshotView
