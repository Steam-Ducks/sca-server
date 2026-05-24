from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from budget.selectors import (
    get_budget_indicators,
    get_budget_indicators_gold,
    get_budget_last_updated_at,
    get_budget_last_updated_at_gold,
    get_budget_snapshot,
    get_budget_snapshot_gold,
)
from budget.serializers import (
    BudgetIndicatorsSerializer,
    BudgetProjectSerializer,
    GoldBudgetSnapshotSerializer,
)

_CACHE_TTL = 300


def _ck(prefix, params=None):
    suffix = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()) if v)
    return f"{prefix}:{suffix}" if suffix else prefix


class BudgetSnapshotView(APIView):
    """
    GET /api/budget/

    Returns budget health rows by project with estimated budget,
    actual cost and percentage deviation.

    Reads from gold."budget_snapshot" when populated (fast pre-computed),
    falls back to live Silver queries when the gold table is empty.
    """

    def get(self, request):
        key = _ck("budget_snapshot", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        gold_qs = get_budget_snapshot_gold(request.query_params)

        if gold_qs.exists():
            serializer = GoldBudgetSnapshotSerializer(gold_qs, many=True)
            last_updated_at = get_budget_last_updated_at_gold()
        else:
            rows = get_budget_snapshot(request.query_params)
            serializer = BudgetProjectSerializer(rows, many=True)
            last_updated_at = get_budget_last_updated_at(request.query_params)

        data = {
            "data": serializer.data,
            "last_updated_at": (last_updated_at.isoformat() if last_updated_at else None),
        }
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class BudgetIndicatorsView(APIView):
    """
    GET /api/budget/indicators/

    Returns pre-aggregated KPI indicators for budget and financial health.
    Accepts the same query-param filters as BudgetSnapshotView:
    periodo, programa, projeto, saude.

    Reads from gold."budget_snapshot" when populated (fast pre-computed),
    falls back to live Silver queries when the gold table is empty.
    """

    def get(self, request):
        key = _ck("budget_indicators", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        indicators = get_budget_indicators_gold(request.query_params)

        if indicators is not None:
            last_updated_at = get_budget_last_updated_at_gold()
        else:
            indicators = get_budget_indicators(request.query_params)
            last_updated_at = get_budget_last_updated_at(request.query_params)

        serializer = BudgetIndicatorsSerializer(indicators)

        data = {
            "data": serializer.data,
            "last_updated_at": (last_updated_at.isoformat() if last_updated_at else None),
        }
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
