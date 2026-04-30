# dashboard/views.py
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.selectors import (
    get_cost_composition,
    get_dashboard_kpis,
    get_program_summary,
    get_projects_by_period,
    get_top_projects_by_cost,
)
from dashboard.serializers import (
    CostCompositionSerializer,
    DashboardKPIsSerializer,
    MainDashboardSerializer,
    ProgramSummarySerializer,
    TopProjectSerializer,
)


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

    def get(self, request):
        kpis = get_dashboard_kpis(_normalize_dashboard_filters(request.query_params))
        serializer = DashboardKPIsSerializer(kpis)
        return Response(serializer.data)


class MainDashboardView(APIView):
    """
    GET /api/main-dashboard/

    Returns list of projects filtered by date range.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
    """

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        qs = get_projects_by_period(start_date, end_date)
        serializer = MainDashboardSerializer(qs, many=True)
        return Response(serializer.data)


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

    def get(self, request):
        rows = get_program_summary(_normalize_dashboard_filters(request.query_params))
        serializer = ProgramSummarySerializer(rows, many=True)
        return Response(serializer.data)


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

    def get(self, request):
        data = get_cost_composition(_normalize_dashboard_filters(request.query_params))
        serializer = CostCompositionSerializer(data)
        return Response(serializer.data)


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

    def get(self, request):
        rows = get_top_projects_by_cost(
            _normalize_dashboard_filters(request.query_params)
        )
        serializer = TopProjectSerializer(rows, many=True)
        return Response(serializer.data)
