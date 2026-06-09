from django.db.models import Q
from rest_framework import generics
from django.utils.dateparse import parse_datetime

from audit.serializers import AuditExecutionLogSerializer
from sca_data.models import AuditExecutionLog
from users.permissions import CanAccessAudit, _get_permissao
from core.utils.date_utils import parse_date, parse_period

_ALLOWED_TABLES_BY_PROFILE: dict = {
    "super_admin": None,
    "financeiro": {"programas", "projetos", "tarefas_projeto", "tempo_tarefas"},
    "compras": {
        "fornecedores",
        "pedidos_compra",
        "solicitacoes_compra",
        "compras_projeto",
    },
    "almoxarifado": {"materiais", "empenho_materiais", "estoque_materiais_projeto"},
    "projetos": {"projetos", "tarefas_projeto", "tempo_tarefas"},
}


class AuditExecutionLogTableView(generics.ListAPIView):
    serializer_class = AuditExecutionLogSerializer
    permission_classes = [CanAccessAudit]

    def get_queryset(self):
        queryset = AuditExecutionLog.objects.all()

        perfil = _get_permissao(self.request.user)
        allowed_tables = _ALLOWED_TABLES_BY_PROFILE.get(perfil)
        if allowed_tables is not None:
            queryset = queryset.filter(table_name__in=allowed_tables)

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
                    started_at__date__gte=parse_date(data_inicio, "data_inicio")
                )
            if data_fim:
                queryset = queryset.filter(
                    started_at__date__lte=parse_date(data_fim, "data_fim")
                )
        elif periodo:
            primeiro_dia, ultimo_dia = parse_period(periodo)
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
