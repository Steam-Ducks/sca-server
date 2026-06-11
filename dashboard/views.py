# dashboard/views.py
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import CanAccessDashboard

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
    """
    GET /api/dashboard/kpis/

    Returns the main consolidated indicators of the analytics panel.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — codigo_programa (program name)
        project    — nome_projeto (project name)
        status     — project status
    """

    permission_classes = [CanAccessDashboard]

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
    """
    GET /api/main-dashboard/

    Returns list of projects filtered by date range.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
    """

    permission_classes = [CanAccessDashboard]

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
    """
    GET /api/main-dashboard/summary/

    Returns cost aggregates grouped by program for the main dashboard
    summary table.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        programa   — program name
        projeto    — project name
    """

    permission_classes = [CanAccessDashboard]

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
    """
    GET /api/main-dashboard/composition/

    Returns the overall cost composition split between materials and
    technical hours, including percentage breakdown.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        programa   — program name
        projeto    — project name
    """

    permission_classes = [CanAccessDashboard]

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
    """
    GET /api/dashboard/top-projects/

    Returns the top 10 projects ranked by total consolidated cost
    (materials + technical hours).

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (case-insensitive)
        project    — project name (case-insensitive)
        status     — project status (case-insensitive)
    """

    permission_classes = [CanAccessDashboard]

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
    """
    GET /api/dashboard/cost-evolution/

    Returns consolidated cost grouped by month (YYYY-MM), ordered
    chronologically. Used for the time-series chart on the main dashboard.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program name (case-insensitive)
        project    — project name (case-insensitive)
        status     — project status (case-insensitive)
    """

    permission_classes = [CanAccessDashboard]

    def get(self, request):
        key = _ck("cost_evolution", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        rows = get_cost_evolution(request.query_params)
        data = CostEvolutionSerializer(rows, many=True).data
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
