import io
import logging

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response

from imports import services
from users.permissions import CanAccessImports, _get_permissao

logger = logging.getLogger(__name__)


class CSVUploadView(APIView):
    csv_type: str = None
    permission_classes = [CanAccessImports]

    def post(self, request):
        perfil = _get_permissao(request.user)
        services.check_profile_access(perfil, self.csv_type)

        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Nenhum arquivo enviado."}, status=400)

        if not file.name.lower().endswith(".csv"):
            return Response(
                {"error": "Apenas arquivos .csv são aceitos."},
                status=400,
            )

        if file.size > services._MAX_UPLOAD_BYTES:
            mb = services._MAX_UPLOAD_BYTES // (1024 * 1024)
            return Response(
                {"error": f"Arquivo excede o limite de {mb} MB."},
                status=400,
            )

        try:
            df = pd.read_csv(io.BytesIO(file.read()), dtype=str, keep_default_na=False)
        except Exception as exc:
            return Response({"error": f"Falha ao ler CSV: {exc}"}, status=400)

        column_error = services.validate_csv_columns(df, self.csv_type)
        if column_error:
            return Response(column_error, status=400)

        try:
            result = services.ingest_csv(df, self.csv_type, file.name)
        except RuntimeError as exc:
            return Response({"error": str(exc)}, status=500)

        return Response(result)


class ProgramasUploadView(CSVUploadView):
    csv_type = "programas"


class ProjetosUploadView(CSVUploadView):
    csv_type = "projetos"


class MateriaisUploadView(CSVUploadView):
    csv_type = "materiais"


class EmpenhoMateriaisUploadView(CSVUploadView):
    csv_type = "empenho_materiais"


class EstoqueMateriaisProjetoUploadView(CSVUploadView):
    csv_type = "estoque_materiais_projeto"


class FornecedoresUploadView(CSVUploadView):
    csv_type = "fornecedores"


class PedidosCompraUploadView(CSVUploadView):
    csv_type = "pedidos_compra"


class SolicitacoesCompraUploadView(CSVUploadView):
    csv_type = "solicitacoes_compra"


class ComprasProjetoUploadView(CSVUploadView):
    csv_type = "compras_projeto"


class TarefasProjetoUploadView(CSVUploadView):
    csv_type = "tarefas_projeto"


class TempoTarefasUploadView(CSVUploadView):
    csv_type = "tempo_tarefas"
