"""
Utilitários para construção padronizada de filtros Django.
"""

from rest_framework.exceptions import ValidationError

from core.utils.date_utils import parse_date, parse_period


def build_date_filters(
    params,
    *,
    field: str,
    start_param: str = "data_inicio",
    end_param: str = "data_fim",
    period_param: str = "periodo",
    year_param: str = "ano",
    month_param: str = "mes",
    allow_period: bool = True,
    allow_year_month: bool = False,
) -> dict:
    """
    Constrói filtros Django de data a partir de parâmetros de consulta.

    Prioridade: intervalo > período > ano/mês.
    """
    raw_start = params.get(start_param)
    raw_end = params.get(end_param)

    if raw_start or raw_end:
        filters = {}
        if raw_start:
            filters[f"{field}__gte"] = parse_date(raw_start, start_param)
        if raw_end:
            filters[f"{field}__lte"] = parse_date(raw_end, end_param)

        if (
            raw_start
            and raw_end
            and filters[f"{field}__gte"] > filters[f"{field}__lte"]
        ):
            raise ValidationError(
                {start_param: f"{start_param} não pode ser posterior a {end_param}."}
            )

        return filters

    raw_period = params.get(period_param)
    if allow_period and raw_period:
        first_day, last_day = parse_period(raw_period)
        return {
            f"{field}__gte": first_day,
            f"{field}__lte": last_day,
        }

    if allow_year_month:
        filters = {}
        raw_year = params.get(year_param)
        raw_month = params.get(month_param)

        if raw_year:
            try:
                filters[f"{field}__year"] = int(raw_year)
            except (TypeError, ValueError):
                raise ValidationError({year_param: "Deve ser um número inteiro."})

        if raw_month:
            try:
                filters[f"{field}__month"] = int(raw_month)
            except (TypeError, ValueError):
                raise ValidationError({month_param: "Deve ser um número inteiro."})

        return filters

    return {}
