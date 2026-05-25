import io
import logging
import uuid
import datetime

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response

from sca_data.db.enums import OperationStatus, OperationType, LayerSchema
from imports.schemas import REQUIRED_COLUMNS

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

_engine = None
audit_mod = None


def _get_engine():
    global _engine, audit_mod
    if _engine is None:
        from sca_data.db.connection import get_or_create
        import sca_data.db.audit.audit as _am

        audit_mod = _am
        _engine = get_or_create()
        audit_mod.create_audit(_engine)
    return _engine


def _audit(
    engine, run_id, operation, status, schema, table, rows, started_at, meta=None
):
    try:
        audit_mod.log_exec(
            engine=engine,
            run_id=run_id,
            operation=operation,
            status=status,
            table_schema=schema,
            table_name=table,
            affected_rows=rows,
            started_at=started_at,
            metadata=meta,
        )
    except Exception:
        logger.exception("Audit logging failed for %s", table)


def _validate_rows(df):
    """Count error and warning rows in the dataframe.

    Erros: rows with at least one empty/null required value.
    Avisos: rows where a non-empty cell contains only whitespace.
    """
    erros = int(df.isnull().any(axis=1).sum() + (df == "").any(axis=1).sum())
    avisos = int(
        df.apply(lambda col: col.str.strip().eq("") & col.ne(""), axis=0)
        .any(axis=1)
        .sum()
    )
    return erros, avisos


def _register_execucao(
    run_id,
    tabela,
    status,
    linhas,
    erros,
    avisos,
    detalhes,
    iniciado_em,
    tipo_processo="COMPLETA",
):
    try:
        from sca_data.models import FatoExecucaoCarga

        FatoExecucaoCarga.objects.create(
            run_id=run_id,
            fonte="csv_upload",
            tabela=tabela,
            tipo_processo=tipo_processo,
            status=status,
            linhas_processadas=linhas,
            erros=erros,
            avisos=avisos,
            detalhes_falha=detalhes,
            iniciado_em=iniciado_em,
            finalizado_em=datetime.datetime.now(),
        )
    except Exception:
        logger.exception("Failed to register execucao_carga for %s", tabela)


class CSVUploadView(APIView):
    csv_type: str = None

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Nenhum arquivo enviado."}, status=400)

        if not file.name.lower().endswith(".csv"):
            return Response(
                {"error": "Apenas arquivos .csv são aceitos."},
                status=400,
            )

        if file.size > _MAX_UPLOAD_BYTES:
            mb = _MAX_UPLOAD_BYTES // (1024 * 1024)
            return Response(
                {"error": f"Arquivo excede o limite de {mb} MB."},
                status=400,
            )

        try:
            df = pd.read_csv(io.BytesIO(file.read()), dtype=str, keep_default_na=False)
        except Exception as exc:
            return Response({"error": f"Falha ao ler CSV: {exc}"}, status=400)

        expected = REQUIRED_COLUMNS[self.csv_type]
        actual = set(df.columns.str.strip())
        missing = expected - actual
        if missing:
            return Response(
                {
                    "error": "Arquivo incompatível com o tipo esperado.",
                    "tipo_esperado": self.csv_type,
                    "colunas_ausentes": sorted(missing),
                },
                status=400,
            )

        erros, avisos = _validate_rows(df)

        engine = _get_engine()
        run_id = str(uuid.uuid4())
        started_at = datetime.datetime.now()

        # Lazy imports avoid the module-level ENGINE = get_or_create() side
        # effect in bronze/silver ingestion modules running during test collection.
        from sca_data.db.bronze.ingestion import (
            _create_table as _bronze_create_table,
            _ensure_schema as _ensure_bronze_schema,
        )
        from sca_data.db.silver.ingestion_silver import (
            PIPELINE as _SILVER_PIPELINE,
            _ensure_schema as _ensure_silver_schema,
        )

        try:
            _ensure_bronze_schema(engine)
            _bronze_create_table(df.copy(), engine, self.csv_type)
        except Exception as exc:
            logger.exception("Bronze ingestion failed for %s", self.csv_type)
            _audit(
                engine,
                run_id,
                OperationType.INGEST,
                OperationStatus.FAILED,
                LayerSchema.BRONZE,
                self.csv_type,
                0,
                started_at,
                {"source": "csv_upload", "filename": file.name, "error": str(exc)},
            )
            _register_execucao(
                run_id,
                self.csv_type,
                OperationStatus.FAILED,
                0,
                erros,
                avisos,
                str(exc),
                started_at,
            )
            return Response(
                {"error": f"Erro ao salvar dados brutos: {exc}"}, status=500
            )

        _audit(
            engine,
            run_id,
            OperationType.INGEST,
            OperationStatus.SUCCESS,
            LayerSchema.BRONZE,
            self.csv_type,
            len(df),
            started_at,
            {"source": "csv_upload", "filename": file.name},
        )

        silver_fn = dict(_SILVER_PIPELINE).get(self.csv_type)
        silver_failed = False
        silver_error = None
        if silver_fn:
            try:
                _ensure_silver_schema(engine)

                def _log_silver(
                    table_name, op_status, st, affected_rows=0, metadata=None
                ):
                    _audit(
                        engine,
                        run_id,
                        OperationType.TRANSFORM,
                        op_status,
                        LayerSchema.SILVER,
                        table_name,
                        affected_rows,
                        st,
                        metadata,
                    )

                silver_fn(engine, run_id, _log_silver)
            except Exception as exc:
                logger.exception("Silver transform failed for %s", self.csv_type)
                silver_failed = True
                silver_error = str(exc)

        if silver_failed:
            final_status = OperationStatus.PARTIAL
        else:
            final_status = OperationStatus.SUCCESS

        _register_execucao(
            run_id,
            self.csv_type,
            final_status,
            len(df),
            erros,
            avisos,
            silver_error,
            started_at,
        )

        return Response(
            {
                "run_id": run_id,
                "tabela": self.csv_type,
                "linhas_recebidas": len(df),
            }
        )


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
