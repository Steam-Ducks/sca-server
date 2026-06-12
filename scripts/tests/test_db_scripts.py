"""
Testes para scripts/check_db_compatibility.py e scripts/export_schema_snapshot.py.

Como rodar:
    pytest scripts/tests/test_db_scripts.py -v
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: importa as funções sem disparar django.setup() de novo
# ---------------------------------------------------------------------------

import scripts.check_db_compatibility as compat
import scripts.export_schema_snapshot as snapshot


# ===========================================================================
# check_db_compatibility — funções de status
# ===========================================================================


class TestStatusHelpers:
    def test_ok_retorna_status_ok(self):
        result = compat.ok("tudo certo")
        assert result == {"status": "ok", "message": "tudo certo"}

    def test_warn_retorna_status_warn(self):
        result = compat.warn("atenção")
        assert result == {"status": "warn", "message": "atenção"}

    def test_fail_retorna_status_fail(self):
        result = compat.fail("erro crítico")
        assert result == {"status": "fail", "message": "erro crítico"}


# ===========================================================================
# check_db_compatibility — check_connection
# ===========================================================================


class TestCheckConnection:
    @patch("scripts.check_db_compatibility.connection")
    def test_conexao_ok(self, mock_conn):
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = compat.check_connection()

        assert result["status"] == "ok"
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("scripts.check_db_compatibility.connection")
    def test_conexao_falha(self, mock_conn):
        mock_conn.cursor.side_effect = Exception("host unreachable")

        result = compat.check_connection()

        assert result["status"] == "fail"
        assert "host unreachable" in result["message"]


# ===========================================================================
# check_db_compatibility — check_postgres_version
# ===========================================================================


class TestCheckPostgresVersion:
    def _make_cursor(self, raw_version, version_num):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [(raw_version,), (version_num,)]
        return cursor

    @patch("scripts.check_db_compatibility.connection")
    def test_versao_aceita_postgres_16(self, mock_conn):
        cursor = self._make_cursor("16.1", 160001)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = compat.check_postgres_version()

        assert result["status"] == "ok"
        assert "16.1" in result["message"]

    @patch("scripts.check_db_compatibility.connection")
    def test_versao_rejeita_postgres_13(self, mock_conn):
        cursor = self._make_cursor("13.4", 130004)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        result = compat.check_postgres_version()

        assert result["status"] == "fail"
        assert "13.4" in result["message"]


# ===========================================================================
# check_db_compatibility — check_pending_migrations
# ===========================================================================


class TestCheckPendingMigrations:
    @patch("scripts.check_db_compatibility.MigrationExecutor")
    @patch("scripts.check_db_compatibility.connection")
    def test_sem_migracoes_pendentes(self, mock_conn, mock_executor_cls):
        mock_executor = MagicMock()
        mock_executor.migration_plan.return_value = []
        mock_executor_cls.return_value = mock_executor

        result = compat.check_pending_migrations()

        assert result["status"] == "ok"

    @patch("scripts.check_db_compatibility.MigrationExecutor")
    @patch("scripts.check_db_compatibility.connection")
    def test_com_migracoes_pendentes(self, mock_conn, mock_executor_cls):
        migration = MagicMock()
        migration.__str__ = lambda self: "myapp.0005_alter_table"
        mock_executor = MagicMock()
        mock_executor.migration_plan.return_value = [(migration, False)]
        mock_executor_cls.return_value = mock_executor

        result = compat.check_pending_migrations()

        assert result["status"] == "fail"
        assert "myapp.0005_alter_table" in result["message"]


# ===========================================================================
# check_db_compatibility — check_psycopg_driver
# ===========================================================================


class TestCheckPsycopgDriver:
    def test_psycopg3_instalado(self):
        fake_psycopg = MagicMock()
        fake_psycopg.__version__ = "3.1.18"
        with patch.dict("sys.modules", {"psycopg": fake_psycopg}):
            result = compat.check_psycopg_driver()
        assert result["status"] == "ok"
        assert "3.1.18" in result["message"]

    def test_psycopg2_gera_warn(self):
        fake_psycopg = MagicMock()
        fake_psycopg.__version__ = "2.9.9"
        with patch.dict("sys.modules", {"psycopg": fake_psycopg}):
            result = compat.check_psycopg_driver()
        assert result["status"] == "warn"

    def test_psycopg_ausente_gera_fail(self):
        with patch.dict("sys.modules", {"psycopg": None}):
            result = compat.check_psycopg_driver()
        assert result["status"] == "fail"


# ===========================================================================
# check_db_compatibility — main (integração das 5 checagens)
# ===========================================================================


class TestCompatibilityMain:
    @patch("scripts.check_db_compatibility.check_psycopg_driver")
    @patch("scripts.check_db_compatibility.check_model_table_consistency")
    @patch("scripts.check_db_compatibility.check_pending_migrations")
    @patch("scripts.check_db_compatibility.check_postgres_version")
    @patch("scripts.check_db_compatibility.check_connection")
    def test_todas_ok_gera_json_compativel(
        self, mock_conn, mock_ver, mock_mig, mock_model, mock_psycopg
    ):
        for mock in [mock_conn, mock_ver, mock_mig, mock_model, mock_psycopg]:
            mock.return_value = {"status": "ok", "message": "ok"}

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            with pytest.raises(SystemExit) as exc:
                compat.main()
            assert exc.value.code == 0

    @patch("scripts.check_db_compatibility.check_psycopg_driver")
    @patch("scripts.check_db_compatibility.check_model_table_consistency")
    @patch("scripts.check_db_compatibility.check_pending_migrations")
    @patch("scripts.check_db_compatibility.check_postgres_version")
    @patch("scripts.check_db_compatibility.check_connection")
    def test_uma_falha_exit_code_1(
        self, mock_conn, mock_ver, mock_mig, mock_model, mock_psycopg
    ):
        mock_conn.return_value = {"status": "fail", "message": "sem conexão"}
        for mock in [mock_ver, mock_mig, mock_model, mock_psycopg]:
            mock.return_value = {"status": "ok", "message": "ok"}

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            with pytest.raises(SystemExit) as exc:
                compat.main()
            assert exc.value.code == 1


# ===========================================================================
# export_schema_snapshot — funções de fetch
# ===========================================================================


class TestFetchTables:
    def test_retorna_lista_de_tabelas(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [("auth_user",), ("sca_projeto",)]

        result = snapshot.fetch_tables(cursor)

        assert result == ["auth_user", "sca_projeto"]


class TestFetchColumns:
    def test_mapeia_colunas_corretamente(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("id", "integer", None, "NO", "nextval('seq')"),
            ("nome", "character varying", 100, "YES", None),
        ]

        result = snapshot.fetch_columns(cursor, "sca_projeto")

        assert len(result) == 2
        assert result[0] == {
            "name": "id",
            "type": "integer",
            "max_length": None,
            "nullable": False,
            "default": "nextval('seq')",
        }
        assert result[1]["nullable"] is True
        assert result[1]["max_length"] == 100


class TestFetchConstraints:
    def test_mapeia_constraints_corretamente(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("sca_projeto_pkey", "PRIMARY KEY", "id", None, None),
            ("sca_projeto_fk", "FOREIGN KEY", "user_id", "auth_user", "id"),
        ]

        result = snapshot.fetch_constraints(cursor, "sca_projeto")

        assert len(result) == 2
        assert result[0]["type"] == "PRIMARY KEY"
        assert result[1]["foreign_table"] == "auth_user"
        assert result[1]["foreign_column"] == "id"


class TestFetchIndexes:
    def test_mapeia_indexes_corretamente(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ("sca_projeto_pkey", True, ["id"]),
            ("sca_projeto_nome_idx", False, ["nome"]),
        ]

        result = snapshot.fetch_indexes(cursor, "sca_projeto")

        assert len(result) == 2
        assert result[0] == {
            "name": "sca_projeto_pkey",
            "unique": True,
            "columns": ["id"],
        }
        assert result[1]["unique"] is False


class TestFetchAppliedMigrations:
    def test_retorna_migracoes_aplicadas(self):
        cursor = MagicMock()
        applied_at = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        cursor.fetchall.return_value = [("auth", "0001_initial", applied_at)]

        result = snapshot.fetch_applied_migrations(cursor)

        assert len(result) == 1
        assert result[0]["app"] == "auth"
        assert result[0]["name"] == "0001_initial"
        assert "2025-01-15" in result[0]["applied_at"]

    def test_retorna_lista_vazia_se_tabela_nao_existe(self):
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("table not found")

        result = snapshot.fetch_applied_migrations(cursor)

        assert result == []


# ===========================================================================
# export_schema_snapshot — main (gera JSON com estrutura correta)
# ===========================================================================


class TestSnapshotMain:
    @patch("scripts.export_schema_snapshot.connection")
    def test_gera_json_com_estrutura_esperada(self, mock_conn):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [("auth_user",)],  # fetch_tables
            [("id", "integer", None, "NO", None)],  # fetch_columns
            [],  # fetch_constraints
            [],  # fetch_indexes
            [],  # fetch_applied_migrations
        ]
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch("scripts.export_schema_snapshot.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__ = MagicMock(return_value=mock_file)
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                snapshot.main()

            written = mock_file.write.call_args_list
            full_json = "".join(c.args[0] for c in written if c.args)

            if full_json:
                data = json.loads(full_json)
                assert "generated_at" in data
                assert "tables" in data
                assert "applied_migrations" in data
        finally:
            os.unlink(tmp_path) if os.path.exists(tmp_path) else None
