import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.selectors import get_execucoes_carga
from monitoring.serializers import FatoExecucaoCargaSerializer
from users.access_control import PROFILE_TABLES_ACCESS
from users.permissions import CanAccessMonitoring, _get_permissao

_VALID_STATUSES = {"SUCCESS", "FAILED", "PARTIAL"}


class ExecucaoCargaView(APIView):
    permission_classes = [CanAccessMonitoring]

    def get(self, request):
        status = request.query_params.get("status")
        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")
        tabela = request.query_params.get("tabela")
        fonte = request.query_params.get("fonte")

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
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
            tabela=tabela,
            fonte=fonte,
        )

        perfil = _get_permissao(request.user)
        allowed_tables = PROFILE_TABLES_ACCESS.get(perfil)
        if allowed_tables is not None:
            execucoes = execucoes.filter(tabela__in=allowed_tables)

        serializer = FatoExecucaoCargaSerializer(execucoes, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})
