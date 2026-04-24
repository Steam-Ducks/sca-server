from rest_framework.views import APIView
from rest_framework.response import Response
from main_dashboard.selectors import get_projects_by_period
from main_dashboard.serializers import MainDashboardSerializer


class MainDashboardView(APIView):
    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        qs = get_projects_by_period(start_date, end_date)

        serializer = MainDashboardSerializer(qs, many=True)

        return Response(serializer.data)