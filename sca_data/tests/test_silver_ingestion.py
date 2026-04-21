import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from sca_data.db.silver.ingestion_silver import (
    PIPELINE,
    _read_bronze,
    _run_pipeline,
    _to_date,
    _to_float,
    _to_int,
    _to_str,
    _transform_compras_projeto,
    _transform_empenho_materiais,
    _transform_estoque_materiais_projeto,
    _transform_fornecedores,
    _transform_materiais,
    _transform_pedidos_compra,
    _transform_programas,
    _transform_projetos,
    _transform_solicitacoes_compra,
    _transform_tarefas_projeto,
    _transform_tempo_tarefas,
    _write_silver,
)


@pytest.fixture
def engine():
    return MagicMock()


@pytest.fixture
def log():
    return MagicMock()


class TestToDate:
    def test_valid_iso_string(self):
        s = pd.Series(["2024-01-15", "2024-06-30"])
        result = _to_date(s)
        assert result[0] == datetime.date(2024, 1, 15)
        assert result[1] == datetime.date(2024, 6, 30)

    def test_invalid_string_becomes_nat(self):
        s = pd.Series(["not-a-date", "abc"])
        result = _to_date(s)
        assert pd.isna(result[0])

    def test_none_becomes_nat(self):
        s = pd.Series([None])
        result = _to_date(s)
        assert pd.isna(result[0])

    def test_already_datetime(self):
        s = pd.Series([datetime.datetime(2024, 3, 10)])
        result = _to_date(s)
        assert result[0] == datetime.date(2024, 3, 10)

    def test_mixed_valid_invalid(self):
        s = pd.Series(["2024-01-01", "invalid", None])
        result = _to_date(s)
        assert result[0] == datetime.date(2024, 1, 1)
        assert pd.isna(result[1])
        assert pd.isna(result[2])


class TestToInt:
    def test_valid_integers(self):
        s = pd.Series([1, 2, 3])
        result = _to_int(s)
        assert result[0] == 1
        assert result[2] == 3

    def test_string_integers(self):
        s = pd.Series(["10", "20"])
        result = _to_int(s)
        assert result[0] == 10

    def test_invalid_becomes_na(self):
        s = pd.Series(["abc", None])
        result = _to_int(s)
        assert pd.isna(result[0])
        assert pd.isna(result[1])

    def test_float_truncated_to_int(self):
        s = pd.Series([1.9, 2.1])
        result = _to_int(s)
        assert result[0] == 1
        assert result[1] == 2

    def test_returns_int64_dtype(self):
        s = pd.Series([1, 2])
        result = _to_int(s)
        assert str(result.dtype) == "Int64"


class TestToFloat:
    def test_valid_floats(self):
        s = pd.Series(["1.5", "2.75"])
        result = _to_float(s)
        assert result[0] == 1.5
        assert result[1] == 2.75

    def test_integer_strings(self):
        s = pd.Series(["100", "0"])
        result = _to_float(s)
        assert result[0] == 100.0

    def test_invalid_becomes_nan(self):
        s = pd.Series(["abc", None])
        result = _to_float(s)
        assert pd.isna(result[0])
        assert pd.isna(result[1])

    def test_negative_values(self):
        s = pd.Series(["-3.14"])
        result = _to_float(s)
        assert result[0] == pytest.approx(-3.14)


class TestToStr:
    def test_strips_whitespace(self):
        s = pd.Series(["  hello  ", " world"])
        result = _to_str(s)
        assert result[0] == "hello"
        assert result[1] == "world"

    def test_nan_string_becomes_none(self):
        s = pd.Series(["nan"])
        result = _to_str(s)
        assert result[0] is None

    def test_none_string_becomes_none(self):
        s = pd.Series(["None"])
        result = _to_str(s)
        assert result[0] is None

    def test_na_tag_becomes_none(self):
        s = pd.Series(["<NA>"])
        result = _to_str(s)
        assert result[0] is None

    def test_actual_none_becomes_none(self):
        s = pd.Series([None])
        result = _to_str(s)
        assert result[0] is None

    def test_max_len_truncates(self):
        s = pd.Series(["abcdefghij"])
        result = _to_str(s, max_len=3)
        assert result[0] == "abc"

    def test_max_len_shorter_than_string_no_truncation(self):
        s = pd.Series(["hi"])
        result = _to_str(s, max_len=10)
        assert result[0] == "hi"

    def test_normal_string_unchanged(self):
        s = pd.Series(["Fornecedor ABC"])
        result = _to_str(s)
        assert result[0] == "Fornecedor ABC"


class TestReadBronze:
    @patch("sca_data.db.silver.ingestion_silver.pd.read_sql")
    def test_reads_correct_table(self, mock_read_sql, engine):
        expected_df = pd.DataFrame({"id": [1]})
        mock_read_sql.return_value = expected_df

        result = _read_bronze(engine, "programas")

        mock_read_sql.assert_called_once()
        sql_arg = mock_read_sql.call_args[0][0]
        assert "programas" in sql_arg
        assert "bronze" in sql_arg
        pd.testing.assert_frame_equal(result, expected_df)


class TestWriteSilver:
    @patch("sca_data.db.silver.ingestion_silver.pd.DataFrame.to_sql")
    def test_adds_ingested_at_column(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1], "nome": ["teste"]})
        _write_silver(df, engine, "programas")

        assert "silver_ingested_at" in df.columns

    @patch("sca_data.db.silver.ingestion_silver.pd.DataFrame.to_sql")
    def test_writes_to_silver_schema(self, mock_to_sql, engine):
        df = pd.DataFrame({"id": [1]})
        _write_silver(df, engine, "programas")

        mock_to_sql.assert_called_once()
        _, kwargs = mock_to_sql.call_args
        assert kwargs["schema"] == "silver"
        assert kwargs["if_exists"] == "append"
        assert kwargs["index"] is False


def _make_engine_with_df(df: pd.DataFrame):
    """Returns (engine, read_mock, write_mock) with _read_bronze patched."""
    engine = MagicMock()
    return engine, df


class TestTransformProgramas:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [1],
                "codigo_programa": ["PRG-001"],
                "nome_programa": ["Programa Alpha"],
                "gerente_programa": ["Ana"],
                "gerente_tecnico": ["Bruno"],
                "data_inicio": ["2024-01-01"],
                "data_fim_prevista": ["2024-12-31"],
                "status": ["Ativo"],
            }
        )

        _transform_programas(MagicMock(), "test-run-id", log)

        mock_write.assert_called_once()
        df_out = mock_write.call_args[0][0]
        assert df_out["codigo_programa"][0] == "PRG-001"
        assert df_out["id"][0] == 1

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_programas(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformMateriais:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [2],
                "codigo_material": ["MAT-001"],
                "descricao": ["Cabo UTP"],
                "categoria": ["Rede"],
                "fabricante": ["Cisco"],
                "custo_estimado": ["150.50"],
                "status": ["Ativo"],
            }
        )

        _transform_materiais(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["codigo_material"][0] == "MAT-001"
        assert df_out["custo_estimado"][0] == pytest.approx(150.50)

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_materiais(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformFornecedores:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [3],
                "codigo_fornecedor": ["FOR-001"],
                "razao_social": ["Tech Ltda"],
                "cidade": ["São Paulo"],
                "estado": ["SP"],
                "categoria": ["TI"],
                "status": ["Ativo"],
            }
        )

        _transform_fornecedores(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["estado"][0] == "SP"
        assert df_out["codigo_fornecedor"][0] == "FOR-001"

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_estado_truncated_to_2_chars(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [3],
                "codigo_fornecedor": ["FOR-001"],
                "razao_social": ["Tech Ltda"],
                "cidade": ["São Paulo"],
                "estado": ["SPA"],  # 3 chars, should be truncated
                "categoria": ["TI"],
                "status": ["Ativo"],
            }
        )

        _transform_fornecedores(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["estado"][0] == "SP"

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_fornecedores(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformProjetos:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [10],
                "codigo_projeto": ["PRJ-001"],
                "nome_projeto": ["Projeto Alpha"],
                "programa_id": [1],
                "responsavel": ["Carlos"],
                "custo_hora": ["200.0"],
                "data_inicio": ["2024-02-01"],
                "data_fim_prevista": ["2024-11-30"],
                "status": ["Em andamento"],
            }
        )

        _transform_projetos(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["programa_id"][0] == 1
        assert df_out["custo_hora"][0] == pytest.approx(200.0)

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_projetos(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformTarefasProjeto:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [100],
                "codigo_tarefa": ["TAR-001"],
                "projeto_id": [10],
                "titulo": ["Implementar módulo X"],
                "responsavel": ["Diego"],
                "estimativa_horas": ["40"],
                "data_inicio": ["2024-03-01"],
                "data_fim_prevista": ["2024-03-31"],
                "status": ["Aberta"],
            }
        )

        _transform_tarefas_projeto(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["estimativa_horas"][0] == 40
        assert df_out["projeto_id"][0] == 10

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_tarefas_projeto(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformTempoTarefas:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [200],
                "tarefa_id": [100],
                "usuario": ["Eduardo"],
                "data": ["2024-03-10"],
                "horas_trabalhadas": ["8.5"],
            }
        )

        _transform_tempo_tarefas(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["horas_trabalhadas"][0] == pytest.approx(8.5)
        assert df_out["tarefa_id"][0] == 100

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_tempo_tarefas(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformSolicitacoesCompra:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [300],
                "numero_solicitacao": ["SC-001"],
                "projeto_id": [10],
                "material_id": [2],
                "quantidade": ["5"],
                "data_solicitacao": ["2024-04-01"],
                "prioridade": ["Alta"],
                "status": ["Pendente"],
            }
        )

        _transform_solicitacoes_compra(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["numero_solicitacao"][0] == "SC-001"
        assert df_out["quantidade"][0] == 5

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_solicitacoes_compra(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformPedidosCompra:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [400],
                "numero_pedido": ["PC-001"],
                "solicitacao_id": [300],
                "fornecedor_id": [3],
                "data_pedido": ["2024-04-05"],
                "data_previsao_entrega": ["2024-04-20"],
                "valor_total": ["7500.00"],
                "status": ["Aprovado"],
            }
        )

        _transform_pedidos_compra(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["valor_total"][0] == pytest.approx(7500.0)
        assert df_out["fornecedor_id"][0] == 3

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_pedidos_compra(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformComprasProjeto:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [500],
                "pedido_compra_id": [400],
                "projeto_id": [10],
                "valor_alocado": ["3000.00"],
            }
        )

        _transform_compras_projeto(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["valor_alocado"][0] == pytest.approx(3000.0)
        assert df_out["pedido_compra_id"][0] == 400

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_compras_projeto(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformEmpenhoMateriais:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [600],
                "projeto_id": [10],
                "material_id": [2],
                "quantidade_empenhada": ["10"],
                "data_empenho": ["2024-05-01"],
            }
        )

        _transform_empenho_materiais(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["quantidade_empenhada"][0] == 10
        assert df_out["material_id"][0] == 2

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_empenho_materiais(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestTransformEstoqueMateriaisProjeto:
    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_happy_path(self, mock_read, mock_write, log):
        mock_read.return_value = pd.DataFrame(
            {
                "id": [700],
                "projeto_id": [10],
                "material_id": [2],
                "quantidade": ["50"],
                "localizacao": ["Almoxarifado A"],
            }
        )

        _transform_estoque_materiais_projeto(MagicMock(), "test-run-id", log)

        df_out = mock_write.call_args[0][0]
        assert df_out["quantidade"][0] == 50
        assert df_out["localizacao"][0] == "Almoxarifado A"

    @patch("sca_data.db.silver.ingestion_silver._write_silver")
    @patch("sca_data.db.silver.ingestion_silver._read_bronze")
    def test_exception_does_not_propagate(self, mock_read, mock_write, log):
        mock_read.side_effect = Exception("DB error")
        _transform_estoque_materiais_projeto(MagicMock(), "test-run-id", log)
        mock_write.assert_not_called()


class TestPipeline:
    def test_pipeline_has_all_11_tables(self):
        assert len(PIPELINE) == 11

    def test_pipeline_order_respects_fk_dependencies(self):
        names = [name for name, _ in PIPELINE]
        assert names.index("programas") < names.index("projetos")
        assert names.index("projetos") < names.index("tarefas_projeto")
        assert names.index("tarefas_projeto") < names.index("tempo_tarefas")
        assert names.index("projetos") < names.index("solicitacoes_compra")
        assert names.index("materiais") < names.index("solicitacoes_compra")
        assert names.index("solicitacoes_compra") < names.index("pedidos_compra")
        assert names.index("fornecedores") < names.index("pedidos_compra")
        assert names.index("pedidos_compra") < names.index("compras_projeto")

    def test_run_pipeline_calls_all_transform_functions(self):
        engine = MagicMock()
        mock_fn_1 = MagicMock()
        mock_fn_2 = MagicMock()
        fake_pipeline = [("table_a", mock_fn_1), ("table_b", mock_fn_2)]

        with patch("sca_data.db.silver.ingestion_silver.PIPELINE", fake_pipeline):
            with patch("sca_data.db.silver.ingestion_silver.audit.log_exec"):
                _run_pipeline(engine)

        mock_fn_1.assert_called_once()
        mock_fn_2.assert_called_once()