from django.urls import path

from budget.views import BudgetSnapshotView

urlpatterns = [
    path("budget/", BudgetSnapshotView.as_view(), name="budget-snapshot"),
]
