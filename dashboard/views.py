# dashboard/views.py
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.selectors import (
    get_cost_composition,
    get_dashboard_kpis,
    get_program_summary,
    get_projects_by_period,
    get_top_projects_by_cost,
    get_cost_evolution,
)
from dashboard.serializers import (
    CostCompositionSerializer,
    DashboardKPIsSerializer,
    MainDashboardSerializer,
    ProgramSummarySerializer,
    TopProjectSerializer,
    CostEvolutionSerializer,
)

_CACHE_TTL = 300


def _ck(prefix, params=None, **kwargs):
    parts = sorted((params or {}).items())
    extra = sorted(kwargs.items())
    suffix = "&".join(f"{k}={v}" for k, v in parts + extra if v)
    return f"{prefix}:{suffix}" if suffix else prefix


def _normalize_dashboard_filters(query_params):
    """Normalize frontend query params to selector params."""
    return {
        "start_date": query_params.get("start_date"),
        "end_date": query_params.get("end_date"),
        "program": query_params.get("program") or query_params.get("programa"),
        "project": query_params.get("project") or query_params.get("projeto"),
        "status": query_params.get("status"),
    }


class DashboardKPIsView(APIView):
    def get(self, request):
        key = _ck("dashboard_kpis", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        kpis = get_dashboard_kpis(_normalize_dashboard_filters(request.query_params))
        data = DashboardKPIsSerializer(kpis).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class MainDashboardView(APIView):
    def get(self, request):
        key = _ck("main_dashboard", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        qs = get_projects_by_period(start_date, end_date)
        data = MainDashboardSerializer(qs, many=True).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class SummaryTableView(APIView):
    def get(self, request):
        key = _ck("summary_table", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        rows = get_program_summary(_normalize_dashboard_filters(request.query_params))
        data = ProgramSummarySerializer(rows, many=True).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class CostCompositionView(APIView):
    def get(self, request):
        key = _ck("cost_composition", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        composition = get_cost_composition(
            _normalize_dashboard_filters(request.query_params)
        )
        data = CostCompositionSerializer(composition).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class TopProjectsView(APIView):
    def get(self, request):
        key = _ck("top_projects", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        rows = get_top_projects_by_cost(
            _normalize_dashboard_filters(request.query_params)
        )
        data = TopProjectSerializer(rows, many=True).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class CostEvolutionView(APIView):
    def get(self, request):
        key = _ck("cost_evolution", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        rows = get_cost_evolution(request.query_params)
        data = CostEvolutionSerializer(rows, many=True).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
