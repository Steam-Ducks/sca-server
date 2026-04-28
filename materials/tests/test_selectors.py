"""
Testes unitários para materials/selectors.py.

Cobre:
  - _parse_date     : parsing de datas ISO com mensagem de erro contextualizada
  - _parse_periodo  : resolução de YYYY-MM para intervalo de datas
  - _get_date_range : lógica de prioridade entre os parâmetros de período
  - get_materials_queryset : construção do queryset com filtros por período
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError

from materials.selectors import (
    _get_date_range,
    _parse_date,
    _parse_periodo,
    get_materials_queryset,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _q_str(q_obj) -> str:
    """Retorna a representação textual do Q para inspeção nos asserts."""
    return str(q_obj)


def _q_conditions(q_obj) -> dict:
    """Extrai recursivamente todos os pares (campo, valor) de um Q object."""
    result = {}
    for child in q_obj.children:
        if isinstance(child, tuple):
            result[child[0]] = child[1]
        else:
            result.update(_q_conditions(child))
    return result


def _mock_pedido_objects():
    """Retorna mocks encadeados para SilverPedidoCompra.objects."""
    mock_qs = MagicMock()
    mock_qs.filter.return_value = mock_qs
    mock_qs.order_by.return_value = mock_qs
    return mock_qs


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


def test_parse_date_formato_iso_valido():
    resultado = _parse_date("2024-03-15", "data_inicio")
    assert resultado == datetime.date(2024, 3, 15)


def test_parse_date_formato_dd_mm_yyyy_levanta_erro():
    with pytest.raises(DRFValidationError) as exc_info:
        _parse_date("31-03-2024", "data_inicio")
    assert "data_inicio" in exc_info.value.detail


def test_parse_date_string_invalida_levanta_erro():
    with pytest.raises(DRFValidationError) as exc_info:
        _parse_date("nao-e-data", "data_fim")
    assert "data_fim" in exc_info.value.detail


def test_parse_date_preserva_param_name_na_mensagem_de_erro():
    with pytest.raises(DRFValidationError) as exc_info:
        _parse_date("invalido", "campo_qualquer")
    assert "campo_qualquer" in exc_info.value.detail


def test_parse_date_retorna_tipo_date():
    resultado = _parse_date("2024-12-31", "data_fim")
    assert isinstance(resultado, datetime.date)


# ---------------------------------------------------------------------------
# _parse_periodo
# ---------------------------------------------------------------------------


def test_parse_periodo_marco_retorna_intervalo_correto():
    inicio, fim = _parse_periodo("2024-03")
    assert inicio == datetime.date(2024, 3, 1)
    assert fim == datetime.date(2024, 3, 31)


def test_parse_periodo_dezembro_retorna_ultimo_dia_31():
    inicio, fim = _parse_periodo("2024-12")
    assert inicio == datetime.date(2024, 12, 1)
    assert fim == datetime.date(2024, 12, 31)


def test_parse_periodo_janeiro_retorna_ultimo_dia_31():
    inicio, fim = _parse_periodo("2024-01")
    assert inicio == datetime.date(2024, 1, 1)
    assert fim == datetime.date(2024, 1, 31)


def test_parse_periodo_fevereiro_ano_bissexto_retorna_dia_29():
    inicio, fim = _parse_periodo("2024-02")
    assert inicio == datetime.date(2024, 2, 1)
    assert fim == datetime.date(2024, 2, 29)


def test_parse_periodo_fevereiro_ano_nao_bissexto_retorna_dia_28():
    inicio, fim = _parse_periodo("2023-02")
    assert inicio == datetime.date(2023, 2, 1)
    assert fim == datetime.date(2023, 2, 28)


def test_parse_periodo_dezembro_ultimo_dia_ano_seguinte_nao_vaza():
    """Garante que dezembro retorna 31/12 e não vira para o ano seguinte."""
    _, fim = _parse_periodo("2024-12")
    assert fim.year == 2024
    assert fim.month == 12


def test_parse_periodo_mes_invalido_levanta_erro():
    with pytest.raises(DRFValidationError) as exc_info:
        _parse_periodo("2024-13")
    assert "periodo" in exc_info.value.detail


def test_parse_periodo_mes_zero_levanta_erro():
    with pytest.raises(DRFValidationError):
        _parse_periodo("2024-00")


def test_parse_periodo_formato_invertido_levanta_erro():
    with pytest.raises(DRFValidationError):
        _parse_periodo("03-2024")


def test_parse_periodo_formato_sem_separador_levanta_erro():
    with pytest.raises(DRFValidationError):
        _parse_periodo("202403")


def test_parse_periodo_formato_yyyymmdd_levanta_erro():
    with pytest.raises(DRFValidationError):
        _parse_periodo("2024-03-15")


# ---------------------------------------------------------------------------
# _get_date_range
# ---------------------------------------------------------------------------


def test_get_date_range_sem_params_retorna_nulos():
    inicio, fim = _get_date_range({})
    assert inicio is None
    assert fim is None


def test_get_date_range_com_periodo_retorna_mes_completo():
    inicio, fim = _get_date_range({"periodo": "2024-03"})
    assert inicio == datetime.date(2024, 3, 1)
    assert fim == datetime.date(2024, 3, 31)


def test_get_date_range_com_data_inicio_apenas():
    inicio, fim = _get_date_range({"data_inicio": "2024-03-01"})
    assert inicio == datetime.date(2024, 3, 1)
    assert fim is None


def test_get_date_range_com_data_fim_apenas():
    inicio, fim = _get_date_range({"data_fim": "2024-03-31"})
    assert inicio is None
    assert fim == datetime.date(2024, 3, 31)


def test_get_date_range_com_intervalo_completo():
    inicio, fim = _get_date_range(
        {"data_inicio": "2024-03-01", "data_fim": "2024-03-31"}
    )
    assert inicio == datetime.date(2024, 3, 1)
    assert fim == datetime.date(2024, 3, 31)


def test_get_date_range_inicio_posterior_ao_fim_levanta_erro():
    with pytest.raises(DRFValidationError) as exc_info:
        _get_date_range({"data_inicio": "2024-03-31", "data_fim": "2024-03-01"})
    assert "data_inicio" in exc_info.value.detail


def test_get_date_range_data_inicio_tem_prioridade_sobre_periodo():
    """data_inicio/data_fim deve ser usado em vez de periodo."""
    inicio, fim = _get_date_range(
        {"data_inicio": "2024-03-15", "periodo": "2024-01"}
    )
    assert inicio == datetime.date(2024, 3, 15)
    assert fim is None  # periodo foi ignorado, não define data_fim


def test_get_date_range_data_fim_tem_prioridade_sobre_periodo():
    inicio, fim = _get_date_range(
        {"data_fim": "2024-03-31", "periodo": "2024-01"}
    )
    assert inicio is None
    assert fim == datetime.date(2024, 3, 31)


def test_get_date_range_ambas_datas_com_periodo_ignoram_periodo():
    inicio, fim = _get_date_range(
        {"data_inicio": "2024-03-01", "data_fim": "2024-03-31", "periodo": "2024-01"}
    )
    assert inicio == datetime.date(2024, 3, 1)
    assert fim == datetime.date(2024, 3, 31)


# ---------------------------------------------------------------------------
# get_materials_queryset — construção dos filtros por período
# ---------------------------------------------------------------------------


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_retorna_queryset(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    resultado = get_materials_queryset({})

    assert resultado == mock_qs


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_ordena_por_valor_total_desc(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({})

    mock_qs.order_by.assert_called_once_with("-valor_total")


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_select_related_inclui_todos_relacionamentos(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({})

    mock_objects.select_related.assert_called_once_with(
        "solicitacao__material",
        "solicitacao__projeto__programa",
        "fornecedor",
    )


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_sem_periodo_nao_filtra_por_data(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "data_pedido__gte" not in q_arg
    assert "data_pedido__lte" not in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_com_periodo_filtra_gte_e_lte(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"periodo": "2024-03"})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "data_pedido__gte" in q_arg
    assert "data_pedido__lte" in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_com_periodo_usa_datas_corretas_do_mes(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"periodo": "2024-03"})

    conds = _q_conditions(mock_qs.filter.call_args.args[0])
    assert conds["data_pedido__gte"] == datetime.date(2024, 3, 1)
    assert conds["data_pedido__lte"] == datetime.date(2024, 3, 31)


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_com_data_inicio_filtra_gte(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"data_inicio": "2024-03-10"})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "data_pedido__gte" in q_arg
    assert "data_pedido__lte" not in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_com_data_fim_filtra_lte(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"data_fim": "2024-03-20"})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "data_pedido__lte" in q_arg
    assert "data_pedido__gte" not in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_com_intervalo_filtra_gte_e_lte(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"data_inicio": "2024-03-01", "data_fim": "2024-03-31"})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "data_pedido__gte" in q_arg
    assert "data_pedido__lte" in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_data_inicio_tem_prioridade_sobre_periodo(mock_objects):
    """data_inicio/data_fim têm prioridade sobre periodo."""
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    # data_inicio=março e periodo=janeiro: março deve vencer
    get_materials_queryset({"data_inicio": "2024-03-15", "periodo": "2024-01"})

    conds = _q_conditions(mock_qs.filter.call_args.args[0])
    assert conds["data_pedido__gte"] == datetime.date(2024, 3, 15)
    assert "data_pedido__lte" not in conds  # periodo ignorado, nao define lte


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_sempre_aplica_filtro_solicitacao_nao_nula(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({})

    q_arg = _q_str(mock_qs.filter.call_args.args[0])
    assert "solicitacao__isnull" in q_arg


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_periodo_dezembro_usa_data_correta(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"periodo": "2024-12"})

    conds = _q_conditions(mock_qs.filter.call_args.args[0])
    assert conds["data_pedido__gte"] == datetime.date(2024, 12, 1)
    assert conds["data_pedido__lte"] == datetime.date(2024, 12, 31)


@patch("materials.selectors.SilverPedidoCompra.objects")
def test_get_materials_queryset_periodo_fevereiro_bissexto_usa_dia_29(mock_objects):
    mock_qs = _mock_pedido_objects()
    mock_objects.select_related.return_value = mock_qs

    get_materials_queryset({"periodo": "2024-02"})

    conds = _q_conditions(mock_qs.filter.call_args.args[0])
    assert conds["data_pedido__lte"] == datetime.date(2024, 2, 29)
