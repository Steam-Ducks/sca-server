from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from sca_data.db.bronze.ingestion import (
    _build_df,
    _create_table,
    _ensure_schema,
    _make_request,
)

@pytest.fixture
def engine():
    return MagicMock()

class TestEnsureSchema:
    def test_creates_bronze_schema(self, engine):
        mock_conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        _ensure_schema(engine)

        mock_conn.execute.assert_called_once()
        sql_text = str(mock_conn.execute.call_args[0][0])
        assert "bronze" in sql_text.lower()

    def test_commits_transaction(self, engine):
        mock_conn = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        _ensure_schema(engine)

        mock_conn.commit.assert_called_once()


class TestCreateTable:
    @patch("sca_data.db.bronze.ingestion.pd.DataFrame.to_sql")
    def test_adds_bronze_ingested_at_column(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1], "nome": ["item"]})
        _create_table(df, engine, "programas")

        assert "bronze_ingested_at" in df.columns

    @patch("sca_data.db.bronze.ingestion.pd.DataFrame.to_sql")
    def test_writes_to_bronze_schema(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1]})
        _create_table(df, engine, "materiais")

        mock_to_sql.assert_called_once()
        _, kwargs = mock_to_sql.call_args
        assert kwargs["schema"] == "bronze"

    @patch("sca_data.db.bronze.ingestion.pd.DataFrame.to_sql")
    def test_replaces_existing_table(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1]})
        _create_table(df, engine, "materiais")

        _, kwargs = mock_to_sql.call_args
        assert kwargs["if_exists"] == "replace"

    @patch("sca_data.db.bronze.ingestion.pd.DataFrame.to_sql")
    def test_does_not_write_index(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1]})
        _create_table(df, engine, "materiais")

        _, kwargs = mock_to_sql.call_args
        assert kwargs["index"] is False



class TestBuildDf:
    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_fetches_file_from_endpoint(self, mock_get, mock_create):
        mock_get.return_value.json.return_value = [{"id": 1, "nome": "Alpha"}]

        _build_df("http://api.example.com", "programas.parquet")

        mock_get.assert_called_once_with("http://api.example.com/files/programas.parquet")

    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_strips_parquet_extension_from_table_name(self, mock_get, mock_create):
        mock_get.return_value.json.return_value = [{"id": 1}]

        _build_df("http://api.example.com", "programas.parquet")

        _, _, tb_name = mock_create.call_args[0]
        assert tb_name == "programas"
        assert ".parquet" not in tb_name

    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_builds_dataframe_from_json_response(self, mock_get, mock_create):
        mock_get.return_value.json.return_value = [
            {"id": 1, "nome": "Alpha"},
            {"id": 2, "nome": "Beta"},
        ]

        _build_df("http://api.example.com", "programas.parquet")

        df_arg = mock_create.call_args[0][0]
        assert isinstance(df_arg, pd.DataFrame)
        assert len(df_arg) == 2

    @patch("sca_data.db.bronze.ingestion._create_table")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_exception_does_not_propagate(self, mock_get, mock_create):
        mock_get.side_effect = Exception("Network error")

        _build_df("http://api.example.com", "programas.parquet")

        mock_create.assert_not_called()


class TestMakeRequest:
    @patch("sca_data.db.bronze.ingestion._build_df")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_calls_build_df_for_each_file(self, mock_get, mock_build):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            "programas.parquet",
            "materiais.parquet",
        ]

        _make_request("http://api.example.com")

        assert mock_build.call_count == 2
        mock_build.assert_any_call("http://api.example.com", "programas.parquet")
        mock_build.assert_any_call("http://api.example.com", "materiais.parquet")

    @patch("sca_data.db.bronze.ingestion._build_df")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_non_200_status_does_not_call_build_df(self, mock_get, mock_build):
        mock_get.return_value.status_code = 500

        _make_request("http://api.example.com")

        mock_build.assert_not_called()

    @patch("sca_data.db.bronze.ingestion._build_df")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_network_error_does_not_propagate(self, mock_get, mock_build):
        import requests as req_lib
        mock_get.side_effect = req_lib.exceptions.ConnectionError("timeout")

        _make_request("http://api.example.com")

        mock_build.assert_not_called()

    @patch("sca_data.db.bronze.ingestion._build_df")
    @patch("sca_data.db.bronze.ingestion.requests.get")
    def test_empty_file_list_does_nothing(self, mock_get, mock_build):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = []

        _make_request("http://api.example.com")

        mock_build.assert_not_called()
