"""
Testes unitários para materials/selectors.py.

Cobre:
  - _get_date_range : lógica de prioridade entre os parâmetros de período
  - get_materials_queryset : construção do queryset com filtros por período

Nota: Os testes para parse_date() e parse_period() estão em core/tests/test_date_utils.py
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.exceptions import ValidationError as DRFValidationError

from materials.selectors import (
    _get_date_range,
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
# _get_date_range - Lógica de Prioridade
# ---------------------------------------------------------------------------
# Nota: Testes específicos de parse_date() e parse_period() estão em
# core/tests/test_date_utils.py. Aqui testamos apenas a lógica de
# prioridade e integração com _get_date_range().


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
    inicio, fim = _get_date_range({"data_inicio": "2024-03-15", "periodo": "2024-01"})
    assert inicio == datetime.date(2024, 3, 15)
    assert fim is None  # periodo foi ignorado, não define data_fim


def test_get_date_range_data_fim_tem_prioridade_sobre_periodo():
    inicio, fim = _get_date_range({"data_fim": "2024-03-31", "periodo": "2024-01"})
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
def test_get_materials_queryset_select_related_inclui_todos_relacionamentos(
    mock_objects,
):
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
