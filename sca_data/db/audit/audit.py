import logging
from sqlalchemy import text
from sca_data.db.connection import getOrCreate

def create_audit():

    engine = getOrCreate()

    query = ("""
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
    """)

    with engine.begin() as conn:
        conn.execute(text(query))

    logging.info("Schema 'audit' verificado/criado.")
    logging.info("Tabela 'audit.execution_logs' verificado/criado.")

