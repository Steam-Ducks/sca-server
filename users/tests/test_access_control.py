"""Unit tests for users/access_control.py — permission mapping validation."""

import pytest

from users.access_control import PROFILE_TABLES_ACCESS

ALL_PROFILES = {"super_admin", "financeiro", "compras", "almoxarifado", "projetos"}


class TestProfileTablesAccessStructure:
    def test_all_profiles_present(self):
        assert set(PROFILE_TABLES_ACCESS.keys()) == ALL_PROFILES

    def test_super_admin_has_unrestricted_access(self):
        assert PROFILE_TABLES_ACCESS["super_admin"] is None

    def test_restricted_profiles_have_non_empty_sets(self):
        for profile, tables in PROFILE_TABLES_ACCESS.items():
            if profile != "super_admin":
                assert isinstance(tables, set), f"{profile} should be a set"
                assert len(tables) > 0, f"{profile} table set should not be empty"


class TestProfileTablesAccessValues:
    def test_financeiro_tables(self):
        assert PROFILE_TABLES_ACCESS["financeiro"] == {
            "programas",
            "projetos",
            "tarefas_projeto",
            "tempo_tarefas",
        }

    def test_compras_tables(self):
        assert PROFILE_TABLES_ACCESS["compras"] == {
            "fornecedores",
            "pedidos_compra",
            "solicitacoes_compra",
            "compras_projeto",
        }

    def test_almoxarifado_tables(self):
        assert PROFILE_TABLES_ACCESS["almoxarifado"] == {
            "materiais",
            "empenho_materiais",
            "estoque_materiais_projeto",
        }

    def test_projetos_tables(self):
        assert PROFILE_TABLES_ACCESS["projetos"] == {
            "projetos",
            "tarefas_projeto",
            "tempo_tarefas",
        }


class TestProfileTablesAccessLookup:
    def test_unknown_profile_returns_none(self):
        assert PROFILE_TABLES_ACCESS.get("nonexistent") is None

    def test_super_admin_lookup_returns_none(self):
        allowed = PROFILE_TABLES_ACCESS.get("super_admin")
        assert allowed is None

    @pytest.mark.parametrize(
        "profile,table,expected",
        [
            ("financeiro", "programas", True),
            ("financeiro", "fornecedores", False),
            ("compras", "pedidos_compra", True),
            ("compras", "programas", False),
            ("almoxarifado", "materiais", True),
            ("almoxarifado", "projetos", False),
            ("projetos", "tarefas_projeto", True),
            ("projetos", "fornecedores", False),
        ],
    )
    def test_table_access_per_profile(self, profile, table, expected):
        allowed = PROFILE_TABLES_ACCESS.get(profile)
        result = allowed is None or table in allowed
        assert result == expected
