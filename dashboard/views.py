# dashboard/views.py
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.selectors import get_dashboard_kpis
from dashboard.serializers import DashboardKPIsSerializer


class DashboardKPIsView(APIView):
    """
    GET /api/dashboard/kpis/

    Returns the main consolidated indicators of the analytics panel.

    Query params (all optional):
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        program    — program id
        project    — project id
        status     — project status
    """

    def get(self, request):
        kpis = get_dashboard_kpis(request.query_params)
        serializer = DashboardKPIsSerializer(kpis)
        return Response(serializer.data)
    