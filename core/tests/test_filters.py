"""
Testes para o módulo core.utils.filters.
"""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from core.utils.filters import build_date_filters


def test_build_date_filters_sem_params_retorna_dict_vazio():
    assert build_date_filters({}, field="data") == {}


def test_build_date_filters_com_data_inicio_retorna_gte():
    result = build_date_filters({"data_inicio": "2024-03-01"}, field="data")
    assert result == {"data__gte": datetime.date(2024, 3, 1)}


def test_build_date_filters_com_data_fim_retorna_lte():
    result = build_date_filters({"data_fim": "2024-03-31"}, field="data")
    assert result == {"data__lte": datetime.date(2024, 3, 31)}


def test_build_date_filters_com_intervalo_completo_retorna_gte_e_lte():
    result = build_date_filters(
        {"data_inicio": "2024-03-01", "data_fim": "2024-03-31"},
        field="data",
    )
    assert result == {
        "data__gte": datetime.date(2024, 3, 1),
        "data__lte": datetime.date(2024, 3, 31),
    }


def test_build_date_filters_rejeita_data_inicio_posterior_a_data_fim():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters(
            {"data_inicio": "2024-03-31", "data_fim": "2024-03-01"},
            field="data",
        )

    assert "data_inicio" in exc_info.value.detail


def test_build_date_filters_rejeita_data_inicio_invalida():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters({"data_inicio": "2024-99-01"}, field="data")

    assert "data_inicio" in exc_info.value.detail


def test_build_date_filters_rejeita_data_fim_invalida():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters({"data_fim": "2024-02-99"}, field="data")

    assert "data_fim" in exc_info.value.detail


def test_build_date_filters_com_periodo_retorna_intervalo_do_mes():
    result = build_date_filters({"periodo": "2024-03"}, field="data")
    assert result == {
        "data__gte": datetime.date(2024, 3, 1),
        "data__lte": datetime.date(2024, 3, 31),
    }


def test_build_date_filters_com_periodo_fevereiro_bissexto():
    result = build_date_filters({"periodo": "2024-02"}, field="data")
    assert result["data__lte"] == datetime.date(2024, 2, 29)


def test_build_date_filters_rejeita_periodo_invalido():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters({"periodo": "2024-13"}, field="data")

    assert "periodo" in exc_info.value.detail


def test_build_date_filters_intervalo_tem_prioridade_sobre_periodo():
    result = build_date_filters(
        {"data_inicio": "2024-03-15", "periodo": "2024-01"},
        field="data",
    )
    assert result == {"data__gte": datetime.date(2024, 3, 15)}


def test_build_date_filters_ignora_periodo_quando_desabilitado():
    result = build_date_filters(
        {"periodo": "2024-03"},
        field="data",
        allow_period=False,
    )
    assert result == {}


def test_build_date_filters_ano_mes_quando_habilitado():
    result = build_date_filters(
        {"ano": "2024", "mes": "3"},
        field="data",
        allow_year_month=True,
    )
    assert result == {"data__year": 2024, "data__month": 3}


def test_build_date_filters_ano_apenas_quando_habilitado():
    result = build_date_filters(
        {"ano": "2024"},
        field="data",
        allow_year_month=True,
    )
    assert result == {"data__year": 2024}


def test_build_date_filters_mes_apenas_quando_habilitado():
    result = build_date_filters(
        {"mes": "3"},
        field="data",
        allow_year_month=True,
    )
    assert result == {"data__month": 3}


def test_build_date_filters_ignora_ano_mes_quando_desabilitado():
    result = build_date_filters({"ano": "2024", "mes": "3"}, field="data")
    assert result == {}


def test_build_date_filters_periodo_tem_prioridade_sobre_ano_mes():
    result = build_date_filters(
        {"periodo": "2024-03", "ano": "2023", "mes": "1"},
        field="data",
        allow_year_month=True,
    )
    assert result == {
        "data__gte": datetime.date(2024, 3, 1),
        "data__lte": datetime.date(2024, 3, 31),
    }


def test_build_date_filters_rejeita_ano_nao_inteiro():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters(
            {"ano": "abcd"},
            field="data",
            allow_year_month=True,
        )

    assert "ano" in exc_info.value.detail


def test_build_date_filters_rejeita_mes_nao_inteiro():
    with pytest.raises(ValidationError) as exc_info:
        build_date_filters(
            {"mes": "marco"},
            field="data",
            allow_year_month=True,
        )

    assert "mes" in exc_info.value.detail


def test_build_date_filters_usa_nome_de_campo_aninhado():
    result = build_date_filters(
        {"data_inicio": "2024-03-01"},
        field="pedido_compra__data_pedido",
    )
    assert result == {"pedido_compra__data_pedido__gte": datetime.date(2024, 3, 1)}


def test_build_date_filters_usa_nomes_customizados_de_parametros():
    result = build_date_filters(
        {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        field="data",
        start_param="start_date",
        end_param="end_date",
    )
    assert result == {
        "data__gte": datetime.date(2024, 1, 1),
        "data__lte": datetime.date(2024, 1, 31),
    }


def test_build_date_filters_usa_period_param_customizado():
    result = build_date_filters(
        {"competencia": "2024-04"},
        field="data",
        period_param="competencia",
    )
    assert result == {
        "data__gte": datetime.date(2024, 4, 1),
        "data__lte": datetime.date(2024, 4, 30),
    }


def test_build_date_filters_usa_year_month_params_customizados():
    result = build_date_filters(
        {"year": "2024", "month": "12"},
        field="data",
        year_param="year",
        month_param="month",
        allow_year_month=True,
    )
    assert result == {"data__year": 2024, "data__month": 12}
