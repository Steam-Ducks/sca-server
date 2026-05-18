from imports.schemas import REQUIRED_COLUMNS

_ALL_TYPES = [
    "programas",
    "projetos",
    "materiais",
    "empenho_materiais",
    "estoque_materiais_projeto",
    "fornecedores",
    "pedidos_compra",
    "solicitacoes_compra",
    "compras_projeto",
    "tarefas_projeto",
    "tempo_tarefas",
]


class TestRequiredColumns:
    def test_all_11_csv_types_present(self):
        assert set(REQUIRED_COLUMNS.keys()) == set(_ALL_TYPES)

    def test_each_type_has_at_least_one_column(self):
        for csv_type, cols in REQUIRED_COLUMNS.items():
            assert len(cols) > 0, f"{csv_type} has no required columns"

    def test_id_column_present_in_every_type(self):
        for csv_type, cols in REQUIRED_COLUMNS.items():
            assert "id" in cols, f"'id' missing from {csv_type}"

    def test_all_column_sets_are_sets(self):
        for csv_type, cols in REQUIRED_COLUMNS.items():
            assert isinstance(cols, set), f"{csv_type} columns should be a set"

    def test_programas_columns(self):
        assert REQUIRED_COLUMNS["programas"] == {
            "id",
            "codigo_programa",
            "nome_programa",
            "gerente_programa",
            "gerente_tecnico",
            "data_inicio",
            "data_fim_prevista",
            "status",
        }

    def test_projetos_has_programa_id_fk(self):
        assert "programa_id" in REQUIRED_COLUMNS["projetos"]

    def test_tempo_tarefas_has_tarefa_id_fk(self):
        assert "tarefa_id" in REQUIRED_COLUMNS["tempo_tarefas"]

    def test_empenho_materiais_has_both_fks(self):
        cols = REQUIRED_COLUMNS["empenho_materiais"]
        assert "projeto_id" in cols
        assert "material_id" in cols
