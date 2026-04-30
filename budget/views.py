from rest_framework.response import Response
from rest_framework.views import APIView

from budget.selectors import (
    get_budget_last_updated_at,
    get_budget_last_updated_at_gold,
    get_budget_snapshot,
    get_budget_snapshot_gold,
)
from budget.serializers import BudgetProjectSerializer, GoldBudgetSnapshotSerializer


class BudgetSnapshotView(APIView):
    """
    GET /api/budget/

    Returns budget health rows by project with estimated budget,
    actual cost and percentage deviation.

    Reads from gold."budget_snapshot" when populated (fast pre-computed),
    falls back to live Silver queries when the gold table is empty.
    """

    def get(self, request):
        gold_qs = get_budget_snapshot_gold(request.query_params)

        if gold_qs.exists():
            serializer = GoldBudgetSnapshotSerializer(gold_qs, many=True)
            last_updated_at = get_budget_last_updated_at_gold()
        else:
            rows = get_budget_snapshot(request.query_params)
            serializer = BudgetProjectSerializer(rows, many=True)
            last_updated_at = get_budget_last_updated_at(request.query_params)

        return Response(
            {
                "data": serializer.data,
                "last_updated_at": (
                    last_updated_at.isoformat() if last_updated_at else None
                ),
            }
        )
