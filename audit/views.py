import datetime

from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_datetime

from audit.serializers import AuditExecutionLogSerializer
from sca_data.models import AuditExecutionLog


class AuditExecutionLogTableView(generics.ListAPIView):
    serializer_class = AuditExecutionLogSerializer

    def _parse_periodo(self, raw: str) -> tuple[datetime.date, datetime.date]:
        try:
            if len(raw) != 7 or raw[4] != "-":
                raise ValueError
            year, month = int(raw[:4]), int(raw[5:7])
            if not (1 <= month <= 12):
                raise ValueError
        except (ValueError, IndexError):
            raise ValidationError(
                {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
            )

        primeiro_dia = datetime.date(year, month, 1)
        if month == 12:
            ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        return primeiro_dia, ultimo_dia

    def _parse_date(self, raw: str, param_name: str) -> datetime.date:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            raise ValidationError(
                {param_name: f"Data inválida '{raw}'. Use o formato YYYY-MM-DD."}
            )

    def get_queryset(self):
        queryset = AuditExecutionLog.objects.all()
        params = self.request.query_params

        status = params.get("status")
        operation = params.get("operation")
        programa = params.get("programa")
        projeto = params.get("projeto")
        periodo = params.get("periodo")
        data_inicio = params.get("data_inicio")
        data_fim = params.get("data_fim")
        started_at_gte = params.get("started_at_gte")
        finalized_at_lte = params.get("finalized_at_lte")

        if status:
            queryset = queryset.filter(status=status)

        if operation:
            queryset = queryset.filter(operation=operation)

        if programa:
            queryset = queryset.filter(
                Q(operation_metadata__programa__iexact=programa)
                | Q(operation_metadata__nome_programa__iexact=programa)
            )

        if projeto:
            queryset = queryset.filter(
                Q(operation_metadata__projeto__iexact=projeto)
                | Q(operation_metadata__nome_projeto__iexact=projeto)
            )

        if data_inicio or data_fim:
            if data_inicio:
                queryset = queryset.filter(
                    started_at__date__gte=self._parse_date(data_inicio, "data_inicio")
                )
            if data_fim:
                queryset = queryset.filter(
                    started_at__date__lte=self._parse_date(data_fim, "data_fim")
                )
        elif periodo:
            primeiro_dia, ultimo_dia = self._parse_periodo(periodo)
            queryset = queryset.filter(
                started_at__date__gte=primeiro_dia,
                started_at__date__lte=ultimo_dia,
            )

        if started_at_gte:
            dt = parse_datetime(started_at_gte)
            if dt:
                queryset = queryset.filter(started_at__gte=dt)

        if finalized_at_lte:
            dt = parse_datetime(finalized_at_lte)
            if dt:
                queryset = queryset.filter(finalized_at__lte=dt)

        return queryset.order_by("-started_at")
