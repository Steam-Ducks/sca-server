from rest_framework import generics
from django.utils.dateparse import parse_datetime

from audit.serializers import AuditExecutionLogSerializer
from sca_data.models import AuditExecutionLog


class AuditExecutionLogTableView(generics.ListAPIView):
    serializer_class = AuditExecutionLogSerializer

    def get_queryset(self):
        queryset = AuditExecutionLog.objects.all()

        status = self.request.query_params.get("status")
        operation = self.request.query_params.get("operation")

        started_at_gte = self.request.query_params.get("started_at_gte")

        finalized_at_lte = self.request.query_params.get("finalized_at_lte")

        if status:
            queryset = queryset.filter(status=status)

        if operation:
            queryset = queryset.filter(operation=operation)

        if started_at_gte:
            dt = parse_datetime(started_at_gte)
            if dt:
                queryset = queryset.filter(started_at__gte=dt)

        if finalized_at_lte:
            dt = parse_datetime(finalized_at_lte)
            if dt:
                queryset = queryset.filter(finalized_at__lte=dt)

        return queryset.order_by("-started_at")
