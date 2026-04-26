from rest_framework.response import Response
from rest_framework.views import APIView

from main_dashboard.selectors import (
    get_cost_composition,
    get_program_summary,
    get_projects_by_period,
)
from main_dashboard.serializers import (
    CostCompositionSerializer,
    MainDashboardSerializer,
    ProgramSummarySerializer,
)


class MainDashboardView(APIView):
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
        rows = get_program_summary(request.query_params)
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
        data = get_cost_composition(request.query_params)
        serializer = CostCompositionSerializer(data)
        return Response(serializer.data)
