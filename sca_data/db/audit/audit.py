import datetime
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

_DDL_SCHEMA = "CREATE SCHEMA IF NOT EXISTS audit;"

_DDL_TABLE = """
CREATE TABLE IF NOT EXISTS audit.execution_logs (
    id               SERIAL PRIMARY KEY,
    run_id           UUID NOT NULL,
    operation        VARCHAR(20),
    status           VARCHAR(20),
    table_schema     VARCHAR(100),
    table_name       VARCHAR(100),
    affected_rows    INTEGER,
    started_at       TIMESTAMP,
    finalized_at     TIMESTAMP,
    operation_duration INTEGER,
    operation_metadata JSONB
);
"""


def create_audit(engine):
    try:
        with engine.begin() as conn:
            conn.execute(text(_DDL_SCHEMA))
            conn.execute(text(_DDL_TABLE))
    except Exception:
        logger.exception("Failed to create audit schema/table")


def log_exec(
    engine,
    run_id,
    operation,
    status,
    table_schema,
    table_name,
    affected_rows,
    started_at,
    metadata=None,
):
    finalized_at = datetime.datetime.now()
    duration = None
    if started_at:
        duration = int((finalized_at - started_at).total_seconds())

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO audit.execution_logs
                        (run_id, operation, status, table_schema, table_name,
                         affected_rows, started_at, finalized_at,
                         operation_duration, operation_metadata)
                    VALUES
                        (:run_id, :operation, :status, :table_schema, :table_name,
                         :affected_rows, :started_at, :finalized_at,
                         :duration, :metadata::jsonb)
                    """
                ),
                {
                    "run_id": str(run_id),
                    "operation": str(operation),
                    "status": str(status),
                    "table_schema": str(table_schema) if table_schema else None,
                    "table_name": str(table_name) if table_name else None,
                    "affected_rows": affected_rows,
                    "started_at": started_at,
                    "finalized_at": finalized_at,
                    "duration": duration,
                    "metadata": (
                        __import__("json").dumps(metadata) if metadata else None
                    ),
                },
            )
    except Exception:
        logger.exception("Failed to log audit exec for %s", table_name)
