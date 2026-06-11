import pandas as pd

from imports.views import _validate_rows


class TestValidateRowsErros:
    def test_clean_dataframe_has_zero_erros(self):
        df = pd.DataFrame({"id": ["1", "2"], "nome": ["foo", "bar"]})
        erros, _ = _validate_rows(df)
        assert erros == 0

    def test_empty_string_counted_as_erro(self):
        df = pd.DataFrame({"id": ["1", ""], "nome": ["foo", "bar"]})
        erros, _ = _validate_rows(df)
        assert erros >= 1

    def test_null_value_counted_as_erro(self):
        df = pd.DataFrame({"id": ["1", None], "nome": ["foo", "bar"]})
        erros, _ = _validate_rows(df)
        assert erros >= 1

    def test_multiple_empty_rows_counted(self):
        df = pd.DataFrame({"id": ["", "", "3"], "nome": ["foo", "", "bar"]})
        erros, _ = _validate_rows(df)
        assert erros >= 2

    def test_erros_is_int(self):
        df = pd.DataFrame({"id": ["1"], "nome": ["foo"]})
        erros, _ = _validate_rows(df)
        assert isinstance(erros, int)


class TestValidateRowsAvisos:
    def test_clean_dataframe_has_zero_avisos(self):
        df = pd.DataFrame({"id": ["1", "2"], "nome": ["foo", "bar"]})
        _, avisos = _validate_rows(df)
        assert avisos == 0

    def test_whitespace_only_cell_counted_as_aviso(self):
        df = pd.DataFrame({"id": ["1", "2"], "nome": ["foo", "   "]})
        _, avisos = _validate_rows(df)
        assert avisos >= 1

    def test_empty_string_not_counted_as_aviso(self):
        df = pd.DataFrame({"id": ["1", ""], "nome": ["foo", "bar"]})
        _, avisos = _validate_rows(df)
        assert avisos == 0

    def test_avisos_is_int(self):
        df = pd.DataFrame({"id": ["1"], "nome": ["foo"]})
        _, avisos = _validate_rows(df)
        assert isinstance(avisos, int)

    def test_multiple_whitespace_rows_counted(self):
        df = pd.DataFrame({"id": ["1", "2", "3"], "nome": [" ", "\t", "bar"]})
        _, avisos = _validate_rows(df)
        assert avisos >= 2


class TestValidateRowsReturnType:
    def test_returns_tuple_of_two(self):
        df = pd.DataFrame({"id": ["1"]})
        result = _validate_rows(df)
        assert len(result) == 2

    def test_all_clean_returns_zeros(self):
        df = pd.DataFrame({"id": ["1", "2", "3"], "nome": ["a", "b", "c"]})
        erros, avisos = _validate_rows(df)
        assert erros == 0
        assert avisos == 0
