from unittest.mock import MagicMock, patch

from sca_data.db.schema import SILVER, Silver
from sca_data.db.gold.ingestion_gold import (
    _SQL_BUDGET_SNAPSHOT,
    _SQL_COSTS,
    _SQL_MATERIALS_INDICATORS,
)


def test_silver_schema_name():
    assert SILVER == "silver"


def test_all_table_refs_are_prefixed_with_silver_schema():
    refs = [v for k, v in vars(Silver).items() if not k.startswith("_")]
    assert refs
    for ref in refs:
        assert ref.startswith(f"{SILVER}."), f"{ref!r} does not start with '{SILVER}.'"


def test_silver_projetos():
    assert Silver.PROJETOS == "silver.projetos"


def test_silver_programas():
    assert Silver.PROGRAMAS == "silver.programas"


def test_silver_tarefas_projeto():
    assert Silver.TAREFAS_PROJETO == "silver.tarefas_projeto"


def test_silver_tempo_tarefas():
    assert Silver.TEMPO_TAREFAS == "silver.tempo_tarefas"


def test_silver_compras_projeto():
    assert Silver.COMPRAS_PROJETO == "silver.compras_projeto"


def test_silver_pedidos_compra():
    assert Silver.PEDIDOS_COMPRA == "silver.pedidos_compra"


def test_silver_solicitacoes_compra():
    assert Silver.SOLICITACOES_COMPRA == "silver.solicitacoes_compra"


def test_silver_materiais():
    assert Silver.MATERIAIS == "silver.materiais"


def test_silver_estoque_materiais_projeto():
    assert Silver.ESTOQUE_MATERIAIS_PROJETO == "silver.estoque_materiais_projeto"


# ── Constant usage: ingestion_gold SQL strings ────────────────────────────────


def test_sql_costs_uses_compras_projeto():
    assert Silver.COMPRAS_PROJETO in _SQL_COSTS


def test_sql_costs_uses_projetos():
    assert Silver.PROJETOS in _SQL_COSTS


def test_sql_costs_uses_programas():
    assert Silver.PROGRAMAS in _SQL_COSTS


def test_sql_costs_uses_pedidos_compra():
    assert Silver.PEDIDOS_COMPRA in _SQL_COSTS


def test_sql_materials_indicators_uses_materiais():
    assert Silver.MATERIAIS in _SQL_MATERIALS_INDICATORS


def test_sql_materials_indicators_uses_pedidos_compra():
    assert Silver.PEDIDOS_COMPRA in _SQL_MATERIALS_INDICATORS


def test_sql_budget_snapshot_uses_projetos():
    assert Silver.PROJETOS in _SQL_BUDGET_SNAPSHOT


def test_sql_budget_snapshot_uses_tarefas_projeto():
    assert Silver.TAREFAS_PROJETO in _SQL_BUDGET_SNAPSHOT


def test_sql_budget_snapshot_uses_tempo_tarefas():
    assert Silver.TEMPO_TAREFAS in _SQL_BUDGET_SNAPSHOT


def test_sql_budget_snapshot_uses_compras_projeto():
    assert Silver.COMPRAS_PROJETO in _SQL_BUDGET_SNAPSHOT


# ── Constant usage: dashboard/selectors.py raw SQL ───────────────────────────


def _mock_cursor_kpis():
    cursor = MagicMock()
    cursor.fetchone.side_effect = [(0,), (0,), (0,), (0,)]
    return cursor


def _patch_connection(cursor):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return patch("dashboard.selectors.connection", conn)


def test_dashboard_kpis_sql_uses_compras_projeto():
    from dashboard.selectors import get_dashboard_kpis

    cursor = _mock_cursor_kpis()
    with _patch_connection(cursor):
        get_dashboard_kpis({})
    sql = " ".join(call[0][0] for call in cursor.execute.call_args_list)
    assert Silver.COMPRAS_PROJETO in sql


def test_dashboard_kpis_sql_uses_tempo_tarefas():
    from dashboard.selectors import get_dashboard_kpis

    cursor = _mock_cursor_kpis()
    with _patch_connection(cursor):
        get_dashboard_kpis({})
    sql = " ".join(call[0][0] for call in cursor.execute.call_args_list)
    assert Silver.TEMPO_TAREFAS in sql


def test_dashboard_kpis_sql_uses_projetos():
    from dashboard.selectors import get_dashboard_kpis

    cursor = _mock_cursor_kpis()
    with _patch_connection(cursor):
        get_dashboard_kpis({})
    sql = " ".join(call[0][0] for call in cursor.execute.call_args_list)
    assert Silver.PROJETOS in sql
