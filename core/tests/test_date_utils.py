"""
Testes para o módulo core.utils.date_utils.

Cobertura:
- parse_date() com formatos válidos
- parse_date() com entradas inválidas
- parse_period() com formatos válidos
- parse_period() com entradas inválidas
- Casos de borda (último dia do mês, ano bissexto, etc.)
"""

import datetime

import pytest
from rest_framework.exceptions import ValidationError

from core.utils.date_utils import parse_date, parse_period


# ========================================
# parse_date() - Casos Válidos
# ========================================


def test_parse_date_com_formato_valido():
    """parse_date deve parsear data válida em YYYY-MM-DD."""
    result = parse_date("2024-03-15")
    assert result == datetime.date(2024, 3, 15)


def test_parse_date_janeiro():
    """parse_date deve parsear janeiro corretamente."""
    result = parse_date("2024-01-01")
    assert result == datetime.date(2024, 1, 1)


def test_parse_date_dezembro():
    """parse_date deve parsear dezembro corretamente."""
    result = parse_date("2024-12-31")
    assert result == datetime.date(2024, 12, 31)


def test_parse_date_ano_bissexto_fevereiro():
    """parse_date deve parsear fevereiro 29 em ano bissexto."""
    result = parse_date("2024-02-29")
    assert result == datetime.date(2024, 2, 29)


def test_parse_date_com_parametro_nome_customizado():
    """parse_date com param_name deve usar esse nome na mensagem de erro."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("invalid", param_name="data_inicio")

    assert "data_inicio" in str(exc_info.value)


# ========================================
# parse_date() - Casos Inválidos
# ========================================


def test_parse_date_formato_invalido_mes_invalido():
    """parse_date deve rejeitar mês inválido."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("2024-13-01")

    error = exc_info.value.detail
    assert "data" in error
    assert "inválida" in str(error["data"]).lower()


def test_parse_date_formato_invalido_dia_invalido():
    """parse_date deve rejeitar dia inválido para o mês."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("2024-02-30")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_fevereiro_29_em_ano_nao_bissexto():
    """parse_date deve rejeitar fevereiro 29 em ano não bissexto."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("2023-02-29")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_string_vazia():
    """parse_date deve rejeitar string vazia."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_none():
    """parse_date deve rejeitar None."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date(None)

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_formato_DD_MM_YYYY():
    """parse_date deve rejeitar formato DD-MM-YYYY (ordem invertida)."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("15-03-2024")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_formato_YYYY_MM_DD_com_separadores_diferentes():
    """parse_date deve rejeitar se separadores forem diferentes."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("2024/03/15")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_com_hora():
    """parse_date deve rejeitar formato com hora incluída."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("2024-03-15T10:30:00")

    error = exc_info.value.detail
    assert "data" in error


def test_parse_date_texto_aleatorio():
    """parse_date deve rejeitar texto aleatório."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("not a date")

    error = exc_info.value.detail
    assert "data" in error


# ========================================
# parse_period() - Casos Válidos
# ========================================


def test_parse_period_marco():
    """parse_period deve retornar intervalo correto para março."""
    inicio, fim = parse_period("2024-03")
    assert inicio == datetime.date(2024, 3, 1)
    assert fim == datetime.date(2024, 3, 31)


def test_parse_period_fevereiro_ano_bissexto():
    """parse_period deve retornar 29/02 como último dia em ano bissexto."""
    inicio, fim = parse_period("2024-02")
    assert inicio == datetime.date(2024, 2, 1)
    assert fim == datetime.date(2024, 2, 29)


def test_parse_period_fevereiro_ano_nao_bissexto():
    """parse_period deve retornar 28/02 como último dia em ano não bissexto."""
    inicio, fim = parse_period("2023-02")
    assert inicio == datetime.date(2023, 2, 1)
    assert fim == datetime.date(2023, 2, 28)


def test_parse_period_janeiro():
    """parse_period deve retornar intervalo correto para janeiro."""
    inicio, fim = parse_period("2024-01")
    assert inicio == datetime.date(2024, 1, 1)
    assert fim == datetime.date(2024, 1, 31)


def test_parse_period_dezembro():
    """parse_period deve retornar 31/12 como último dia de dezembro."""
    inicio, fim = parse_period("2024-12")
    assert inicio == datetime.date(2024, 12, 1)
    assert fim == datetime.date(2024, 12, 31)


def test_parse_period_mes_com_30_dias():
    """parse_period deve retornar 30 como último dia para meses com 30 dias."""
    inicio, fim = parse_period("2024-04")
    assert inicio == datetime.date(2024, 4, 1)
    assert fim == datetime.date(2024, 4, 30)


def test_parse_period_anos_diferentes():
    """parse_period deve funcionar com diferentes anos."""
    inicio, fim = parse_period("2000-06")
    assert inicio == datetime.date(2000, 6, 1)
    assert fim == datetime.date(2000, 6, 30)

    inicio, fim = parse_period("2099-06")
    assert inicio == datetime.date(2099, 6, 1)
    assert fim == datetime.date(2099, 6, 30)


# ========================================
# parse_period() - Casos Inválidos
# ========================================


def test_parse_period_formato_invalido_muito_curto():
    """parse_period deve rejeitar string muito curta."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-1")

    error = exc_info.value.detail
    assert "periodo" in error
    assert "YYYY-MM" in str(error["periodo"])


def test_parse_period_formato_invalido_muito_longo():
    """parse_period deve rejeitar string muito longa."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-03-15")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_separador_invalido():
    """parse_period deve rejeitar se separador não for hífen."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024/03")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_mes_00():
    """parse_period deve rejeitar mês 00."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-00")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_mes_13():
    """parse_period deve rejeitar mês 13."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-13")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_mes_99():
    """parse_period deve rejeitar mês 99."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-99")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_ano_invalido():
    """parse_period deve rejeitar ano não-numérico."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("abcd-03")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_mes_invalido_nao_numerico():
    """parse_period deve rejeitar mês não-numérico."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("2024-ab")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_string_vazia():
    """parse_period deve rejeitar string vazia."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("")

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_none():
    """parse_period deve rejeitar None."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period(None)

    error = exc_info.value.detail
    assert "periodo" in error


def test_parse_period_texto_aleatorio():
    """parse_period deve rejeitar texto aleatório."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("not a period")

    error = exc_info.value.detail
    assert "periodo" in error


# ========================================
# Testes de Compatibilidade com Código Anterior
# ========================================


def test_parse_period_resultado_eh_tupla():
    """parse_period deve retornar uma tupla de dates."""
    result = parse_period("2024-03")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], datetime.date)
    assert isinstance(result[1], datetime.date)


def test_parse_date_resultado_eh_date():
    """parse_date deve retornar um datetime.date."""
    result = parse_date("2024-03-15")
    assert isinstance(result, datetime.date)


def test_parse_date_error_message_format():
    """parse_date deve retornar erro com formato esperado."""
    with pytest.raises(ValidationError) as exc_info:
        parse_date("invalid", "custom_param")

    error = exc_info.value.detail
    assert isinstance(error, dict)
    assert "custom_param" in error
    assert "YYYY-MM-DD" in str(error["custom_param"])


def test_parse_period_error_message_format():
    """parse_period deve retornar erro com formato esperado."""
    with pytest.raises(ValidationError) as exc_info:
        parse_period("invalid")

    error = exc_info.value.detail
    assert isinstance(error, dict)
    assert "periodo" in error
    assert "YYYY-MM" in str(error["periodo"])
