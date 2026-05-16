from django.urls import path

from budget.views import BudgetIndicatorsView, BudgetSnapshotView

urlpatterns = [
    path("budget/", BudgetSnapshotView.as_view(), name="budget-snapshot"),
    path(
        "budget/indicators/", BudgetIndicatorsView.as_view(), name="budget-indicators"
    ),
]
