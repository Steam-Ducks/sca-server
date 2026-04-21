import datetime
import logging
import uuid
import pandas as pd
import requests
from sqlalchemy import text
from sca_data.db.connection import getOrCreate
import sca_data.db.audit.audit as audit
from sca_data.db.enums import OperationStatus, OperationType, LayerSchema


logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)


ENGINE = getOrCreate()
ENDPOINT = "https://sca-api-sb1c.onrender.com/"


def _ensure_schema(engine):
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
        conn.commit()
    logging.info("Schema 'bronze' verificado/criado.")


def _create_table(df: pd.DataFrame, engine, tb_name: str):
    logging.info(f"Writing {tb_name} ...")

    df["bronze_ingested_at"] = datetime.datetime.now()

    df.to_sql(
        tb_name,
        engine,
        schema="bronze",
        if_exists="replace",
        index=False,
    )

    logging.info(f"Table {tb_name} wrote in schema 'bronze'!")


def _build_df(endpoint: str, file: str, run_id: str) -> pd.DataFrame:
    
    started_at = datetime.datetime.now()
    table_name = file.replace(".parquet", "")
    route = f"{endpoint}/files/{file}"

    try:

        response = requests.get(route)
        df = pd.DataFrame(response.json())

        logging.info(f"Dataframe built to file {file}.")

        _create_table(df, ENGINE, table_name)

        audit.log_exec(
            engine = ENGINE,
            run_id = run_id,
            operation = OperationType.INGEST,
            status = OperationStatus.SUCCESS,
            table_schema = LayerSchema.BRONZE,
            table_name = table_name,
            affected_rows = len(df),
            started_at = started_at,
            metadata={
                "endpoint": route,
                "columns":  list(df.columns),
            },
        )

    except Exception as e:
        logging.error(f"It was not possible to ingest file {file}. Error {e}")

        audit.log_exec(
            engine = ENGINE,
            run_id = run_id,
            operation = OperationType.INGEST,
            status = OperationStatus.FAILED,
            table_schema = LayerSchema.BRONZE,
            table_name = table_name,
            affected_rows = 0,
            started_at = started_at,
            metadata={
                "endpoint": route,
                "error": str(e),
            },
        )


def _make_request(endpoint: str, run_id: str):
    try:
        response = requests.get(f"{endpoint}/files")

        if response.status_code == 200:
            for item in response.json():
                _build_df(endpoint, item, run_id)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")
        return []


if __name__ == "__main__":
    run_id = str(uuid.uuid4())
    logging.info(f"Run ID: {run_id} ")

    audit.create_audit(ENGINE)
    _ensure_schema(ENGINE)
    _make_request(ENDPOINT, run_id)
