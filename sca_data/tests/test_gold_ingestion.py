import logging
from unittest.mock import MagicMock, patch, call

import pytest


with patch("sca_data.db.connection.getOrCreate", return_value=MagicMock()):
    from sca_data.db.gold.ingestion_gold import (
        _run_budget_snapshot,
        _run_costs,
        _run_materials_indicators,
        _run_pipeline,
    )


def _make_engine(raise_on_execute: Exception | None = None) -> MagicMock:

    conn = MagicMock()
    if raise_on_execute:
        conn.execute.side_effect = raise_on_execute

    engine = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=conn)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine, conn


class TestRunMaterialsIndicators:

    def test_executes_sql_and_commits(self):
        engine, conn = _make_engine()

        _run_materials_indicators(engine)

        conn.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_sql_contains_truncate_and_insert(self):

        engine, conn = _make_engine()

        _run_materials_indicators(engine)

        sql_arg = str(conn.execute.call_args[0][0])
        assert "TRUNCATE" in sql_arg.upper()
        assert "INSERT" in sql_arg.upper()
        assert "indicators_materiais" in sql_arg

    def test_logs_success(self, caplog):
        engine, _ = _make_engine()

        with caplog.at_level(logging.INFO):
            _run_materials_indicators(engine)

        assert any("indicators_materiais" in m for m in caplog.messages)

    def test_catches_exception_and_logs_error(self, caplog):
        engine, _ = _make_engine(raise_on_execute=RuntimeError("DB is down"))

        with caplog.at_level(logging.ERROR):

            _run_materials_indicators(engine)

        assert any("materials_indicators" in m for m in caplog.messages)
        assert any("DB is down" in m for m in caplog.messages)

    def test_does_not_commit_on_error(self):
        engine, conn = _make_engine(raise_on_execute=RuntimeError("oops"))

        _run_materials_indicators(engine)

        conn.commit.assert_not_called()


class TestRunCosts:

    def test_executes_sql_and_commits(self):
        engine, conn = _make_engine()

        _run_costs(engine)

        conn.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_sql_contains_truncate_and_insert(self):
        engine, conn = _make_engine()

        _run_costs(engine)

        sql_arg = str(conn.execute.call_args[0][0])
        assert "TRUNCATE" in sql_arg.upper()
        assert "INSERT" in sql_arg.upper()
        assert "costs" in sql_arg

    def test_logs_success(self, caplog):
        engine, _ = _make_engine()

        with caplog.at_level(logging.INFO):
            _run_costs(engine)

        assert any("costs" in m for m in caplog.messages)

    def test_catches_exception_and_logs_error(self, caplog):
        engine, _ = _make_engine(raise_on_execute=RuntimeError("timeout"))

        with caplog.at_level(logging.ERROR):
            _run_costs(engine)

        assert any("costs" in m for m in caplog.messages)
        assert any("timeout" in m for m in caplog.messages)

    def test_does_not_commit_on_error(self):
        engine, conn = _make_engine(raise_on_execute=RuntimeError("oops"))

        _run_costs(engine)

        conn.commit.assert_not_called()


class TestRunBudgetSnapshot:

    def test_executes_sql_and_commits(self):
        engine, conn = _make_engine()

        _run_budget_snapshot(engine)

        conn.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_sql_contains_truncate_and_insert(self):
        engine, conn = _make_engine()

        _run_budget_snapshot(engine)

        sql_arg = str(conn.execute.call_args[0][0])
        assert "TRUNCATE" in sql_arg.upper()
        assert "INSERT" in sql_arg.upper()
        assert "budget_snapshot" in sql_arg

    def test_sql_contains_saude_financeira_logic(self):
        engine, conn = _make_engine()

        _run_budget_snapshot(engine)

        sql_arg = str(conn.execute.call_args[0][0])
        assert "saude_financeira" in sql_arg.lower() or "Crítico" in sql_arg

    def test_logs_success(self, caplog):
        engine, _ = _make_engine()

        with caplog.at_level(logging.INFO):
            _run_budget_snapshot(engine)

        assert any("budget_snapshot" in m for m in caplog.messages)

    def test_catches_exception_and_logs_error(self, caplog):
        engine, _ = _make_engine(raise_on_execute=RuntimeError("budget error"))

        with caplog.at_level(logging.ERROR):
            _run_budget_snapshot(engine)

        assert any("budget_snapshot" in m for m in caplog.messages)
        assert any("budget error" in m for m in caplog.messages)

    def test_does_not_commit_on_error(self):
        engine, conn = _make_engine(raise_on_execute=RuntimeError("oops"))

        _run_budget_snapshot(engine)

        conn.commit.assert_not_called()


class TestRunPipeline:

    @patch("sca_data.db.gold.ingestion_gold._run_budget_snapshot")
    @patch("sca_data.db.gold.ingestion_gold._run_costs")
    @patch("sca_data.db.gold.ingestion_gold._run_materials_indicators")
    def test_calls_all_steps_in_order(self, mock_materials, mock_costs, mock_budget):
        engine = MagicMock()
        manager = MagicMock()
        manager.attach_mock(mock_materials, "materials")
        manager.attach_mock(mock_costs, "costs")
        manager.attach_mock(mock_budget, "budget")

        _run_pipeline(engine)

        assert manager.mock_calls == [
            call.materials(engine),
            call.costs(engine),
            call.budget(engine),
        ]

    @patch("sca_data.db.gold.ingestion_gold._run_budget_snapshot")
    @patch("sca_data.db.gold.ingestion_gold._run_costs")
    @patch("sca_data.db.gold.ingestion_gold._run_materials_indicators")
    def test_logs_start_and_end(self, _mock_m, _mock_c, _mock_b, caplog):
        with caplog.at_level(logging.INFO):
            _run_pipeline(MagicMock())

        messages = " ".join(caplog.messages)
        assert "Starting" in messages or "starting" in messages.lower()
        assert "Gold" in messages or "gold" in messages.lower()

    @patch(
        "sca_data.db.gold.ingestion_gold._run_costs",
        side_effect=RuntimeError("costs failed"),
    )
    @patch("sca_data.db.gold.ingestion_gold._run_materials_indicators")
    def test_pipeline_propagates_unexpected_error(self, _mock_m, _mock_c):

        with pytest.raises(RuntimeError, match="costs failed"):
            _run_pipeline(MagicMock())
