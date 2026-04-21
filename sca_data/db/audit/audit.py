import json
import logging
import datetime
from sqlalchemy import text


def create_audit(engine):

    query = """
        CREATE SCHEMA IF NOT EXISTS audit;

        CREATE TABLE IF NOT EXISTS audit.execution_logs (
            id SERIAL PRIMARY KEY,
            run_id UUID NOT NULL,
            operation VARCHAR(20) NOT NULL,
            status VARCHAR(20) CHECK (status IN ('SUCCESS','FAILED','PARTIAL')),
            table_schema VARCHAR(100),
            table_name VARCHAR(100),
            affected_rows INTEGER,
            started_at TIMESTAMP NOT NULL,
            finalized_at TIMESTAMP,
            operation_duration INTEGER,
            operation_metadata JSONB
        );
    """

    with engine.begin() as conn:
        conn.execute(text(query))

    logging.info("Schema 'audit' verificado/criado.")
    logging.info("Tabela 'audit.execution_logs' verificado/criado.")


def log_exec(
    engine,
    run_id: str,
    operation: str,
    status: str,
    table_schema: str,
    table_name: str,
    affected_rows: int,
    started_at: datetime.datetime,
    metadata: dict = None,
):
    finalized_at = datetime.datetime.now()
    duration_s = int((finalized_at - started_at).total_seconds())

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit.execution_logs (
                    run_id, 
                    operation, 
                    status, 
                    table_schema,
                    table_name,
                    affected_rows, 
                    started_at, 
                    finalized_at, 
                    operation_duration, 
                    operation_metadata
                )
                VALUES
                    (
                    :run_id, 
                    :operation, 
                    :status, 
                    :table_schema, 
                    :table_name,
                    :affected_rows, 
                    :started_at, 
                    :finalized_at, 
                    :duration, 
                    :metadata
                )
            """
            ),
            {
                "run_id": run_id,
                "operation": operation,
                "status": status,
                "table_schema": table_schema,
                "table_name": table_name,
                "affected_rows": affected_rows,
                "started_at": started_at,
                "finalized_at": finalized_at,
                "duration": duration_s,
                "metadata": json.dumps(metadata) if metadata else None,
            },
        )
