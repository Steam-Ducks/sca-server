import datetime
import logging
import uuid

import pandas as pd
from rest_framework.exceptions import PermissionDenied

from imports.schemas import REQUIRED_COLUMNS
from sca_data.db.enums import OperationStatus, OperationType, LayerSchema

logger = logging.getLogger(__name__)

_ALLOWED_IMPORTS_BY_PROFILE: dict = {
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


def check_profile_access(perfil: str, csv_type: str) -> None:
    """Raises PermissionDenied if perfil is not allowed to import csv_type."""
    allowed = _ALLOWED_IMPORTS_BY_PROFILE.get(perfil)
    if allowed is not None and csv_type not in allowed:
        raise PermissionDenied(
            "Seu perfil não tem permissão para importar este arquivo."
        )


def validate_csv_columns(df: pd.DataFrame, csv_type: str):
    """Returns None if columns are valid, or an error dict if columns are missing."""
    expected = REQUIRED_COLUMNS[csv_type]
    actual = set(df.columns.str.strip())
    missing = expected - actual
    if missing:
        return {
            "error": "Arquivo incompatível com o tipo esperado.",
            "tipo_esperado": csv_type,
            "colunas_ausentes": sorted(missing),
        }
    return None


def ingest_csv(df: pd.DataFrame, csv_type: str, filename: str) -> dict:
    """
    Runs the full ETL pipeline for a validated CSV DataFrame.

    Returns {"run_id": ..., "tabela": ..., "linhas_recebidas": ...}.
    Raises RuntimeError on bronze ingestion failure.
    """
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
        _bronze_create_table(df.copy(), engine, csv_type)
    except Exception as exc:
        logger.exception("Bronze ingestion failed for %s", csv_type)
        _audit(
            engine,
            run_id,
            OperationType.INGEST,
            OperationStatus.FAILED,
            LayerSchema.BRONZE,
            csv_type,
            0,
            started_at,
            {"source": "csv_upload", "filename": filename, "error": str(exc)},
        )
        _register_execucao(
            run_id,
            csv_type,
            OperationStatus.FAILED,
            0,
            erros,
            avisos,
            str(exc),
            started_at,
        )
        raise RuntimeError(f"Erro ao salvar dados brutos: {exc}") from exc

    _audit(
        engine,
        run_id,
        OperationType.INGEST,
        OperationStatus.SUCCESS,
        LayerSchema.BRONZE,
        csv_type,
        len(df),
        started_at,
        {"source": "csv_upload", "filename": filename},
    )

    silver_fn = dict(_SILVER_PIPELINE).get(csv_type)
    silver_failed = False
    silver_error = None
    if silver_fn:
        try:
            _ensure_silver_schema(engine)

            def _log_silver(table_name, op_status, st, affected_rows=0, metadata=None):
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
            logger.exception("Silver transform failed for %s", csv_type)
            silver_failed = True
            silver_error = str(exc)

    final_status = OperationStatus.PARTIAL if silver_failed else OperationStatus.SUCCESS
    _register_execucao(
        run_id,
        csv_type,
        final_status,
        len(df),
        erros,
        avisos,
        silver_error,
        started_at,
    )

    return {
        "run_id": run_id,
        "tabela": csv_type,
        "linhas_recebidas": len(df),
    }
