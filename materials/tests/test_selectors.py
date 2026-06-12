"""
Testes unitários para materials/selectors.py.

Cobre:
  - get_materials_queryset : construção do queryset com filtros por período

Nota: Os testes para construção de filtros de data estão em core/tests/test_filters.py
"""

import datetime
from unittest.mock import MagicMock, patch

from materials.selectors import get_materials_queryset


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
