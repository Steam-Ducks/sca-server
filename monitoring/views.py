import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.selectors import get_execucoes_carga
from monitoring.serializers import FatoExecucaoCargaSerializer
from users.permissions import CanAccessMonitoring, _get_permissao

_VALID_STATUSES = {"SUCCESS", "FAILED", "PARTIAL"}

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


class ExecucaoCargaView(APIView):
    permission_classes = [CanAccessMonitoring]

    def get(self, request):
        status = request.query_params.get("status")
        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")

        if status and status not in _VALID_STATUSES:
            return Response(
                {
                    "error": f"Status inválido. Use: {', '.join(sorted(_VALID_STATUSES))}."
                },
                status=400,
            )

        if data_inicio:
            try:
                data_inicio = datetime.date.fromisoformat(data_inicio)
            except ValueError:
                return Response(
                    {"error": "data_inicio inválida. Use o formato YYYY-MM-DD."},
                    status=400,
                )

        if data_fim:
            try:
                data_fim = datetime.date.fromisoformat(data_fim)
            except ValueError:
                return Response(
                    {"error": "data_fim inválida. Use o formato YYYY-MM-DD."},
                    status=400,
                )

        execucoes = get_execucoes_carga(
            status=status, data_inicio=data_inicio, data_fim=data_fim
        )

        perfil = _get_permissao(request.user)
        allowed_tables = _ALLOWED_TABLES_BY_PROFILE.get(perfil)
        if allowed_tables is not None:
            execucoes = execucoes.filter(tabela__in=allowed_tables)

        serializer = FatoExecucaoCargaSerializer(execucoes, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})
