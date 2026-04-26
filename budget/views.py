from rest_framework.response import Response
from rest_framework.views import APIView

from budget.selectors import get_budget_last_updated_at, get_budget_snapshot
from budget.serializers import BudgetProjectSerializer


class BudgetSnapshotView(APIView):
    """
    GET /api/budget/

    Returns budget health rows by project with estimated budget,
    actual cost and percentage deviation.
    """

    def get(self, request):
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
