"""
Utilitários centralizados para parsing e validação de datas e períodos.

Este módulo fornece funções reutilizáveis para:
- Parse de datas em formato YYYY-MM-DD
- Parse de períodos em formato YYYY-MM
- Validação com mensagens de erro padronizadas
"""

import datetime

from rest_framework.exceptions import ValidationError


def parse_date(raw: str, param_name: str = "data") -> datetime.date:
    """
    Parse uma data no formato YYYY-MM-DD.

    Args:
        raw: String no formato YYYY-MM-DD
        param_name: Nome do parâmetro para mensagem de erro

    Returns:
        datetime.date: Data parseada

    Raises:
        ValidationError: Se formato inválido
    """
    try:
        return datetime.date.fromisoformat(raw)
    except (ValueError, TypeError):
        raise ValidationError(
            {param_name: f"Data inválida '{raw}'. Use o formato YYYY-MM-DD."}
        )


def parse_period(raw: str) -> tuple[datetime.date, datetime.date]:
    """
    Parse um período no formato YYYY-MM para intervalo (primeiro_dia, ultimo_dia).

    Args:
        raw: String no formato YYYY-MM

    Returns:
        tuple: (primeiro_dia, ultimo_dia) como datetime.date

    Raises:
        ValidationError: Se formato inválido
    """
    try:
        if len(raw) != 7 or raw[4] != "-":
            raise ValueError("Formato inválido")
        year, month = int(raw[:4]), int(raw[5:7])
        if not (1 <= month <= 12):
            raise ValueError("Mês inválido")
    except (ValueError, IndexError, TypeError):
        raise ValidationError(
            {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
        )

    primeiro_dia = datetime.date(year, month, 1)
    if month == 12:
        ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    return primeiro_dia, ultimo_dia
