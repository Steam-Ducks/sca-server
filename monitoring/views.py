import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from monitoring.selectors import get_execucoes_carga
from monitoring.serializers import FatoExecucaoCargaSerializer

_VALID_STATUSES = {"SUCCESS", "FAILED", "PARTIAL"}


class ExecucaoCargaView(APIView):
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
        serializer = FatoExecucaoCargaSerializer(execucoes, many=True)
        return Response({"count": len(serializer.data), "results": serializer.data})
