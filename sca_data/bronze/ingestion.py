from sca_data.db.connection import getOrCreate
import pandas as pd
import requests
import logging
import datetime


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)

ENGINE = getOrCreate()
ENDPOINT = "https://sca-api-sb1c.onrender.com/"


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


def _build_df(endpoint: str, file: str) -> pd.DataFrame:
    try:
        response = requests.get(f"{endpoint}/files/{file}")
        df = pd.DataFrame(response.json())

        logging.info(f"Dataframe built to file {file}.")

        _create_table(df, ENGINE, file.replace(".parquet", ""))

    except:
        logging.error(f"It was not possible to ingest file {file}.")


def _make_request(endpoint: str):
    try:
        response = requests.get(f"{endpoint}/files")

        if response.status_code == 200:
            for item in response.json():
                _build_df(endpoint, item)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error: {e}")
        return []


_make_request(ENDPOINT)