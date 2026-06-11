from django.db.models import Count, ExpressionWrapper, F, FloatField, Sum
from django.db.models.functions import TruncMonth

from sca_data.models import SilverTempoTarefa


def get_technical_hours_queryset(params, period_filters=None):
    """
    Returns an annotated queryset of SilverTempoTarefa with all filters applied.

    params         : dict-like (QueryDict or dict) for dimension filters.
    period_filters : pre-built Django filter kwargs for the date field.
                     Pass {} to disable all period filtering (e.g. temporal view).
                     Pass None to let the caller supply no period restriction.
    """
    queryset = (
        SilverTempoTarefa.objects.select_related("tarefa__projeto__programa")
        .filter(tarefa__isnull=False)
        .filter(**(period_filters or {}))
        .annotate(
            custo_por_hora=F("tarefa__projeto__custo_hora"),
            custo_total=ExpressionWrapper(
                F("horas_trabalhadas") * F("tarefa__projeto__custo_hora"),
                output_field=FloatField(),
            ),
        )
    )

    programa = params.get("programa")
    if programa:
        queryset = queryset.filter(
            tarefa__projeto__programa__nome_programa__iexact=programa
        )

    projeto = params.get("projeto")
    if projeto:
        queryset = queryset.filter(tarefa__projeto__nome_projeto__iexact=projeto)

    colaborador = params.get("colaborador")
    if colaborador:
        queryset = queryset.filter(usuario__iexact=colaborador)

    tarefa = params.get("tarefa")
    if tarefa:
        queryset = queryset.filter(tarefa__titulo__iexact=tarefa)

    funcao = params.get("funcao")
    if funcao:
        queryset = queryset.filter(tarefa__responsavel__iexact=funcao)

    return queryset.order_by("-custo_total")


def aggregate_kpis(queryset):
    """Returns KPI aggregates dict from a technical hours queryset."""
    agg = queryset.aggregate(
        total_horas=Sum("horas_trabalhadas"),
        soma_custo=Sum("custo_total"),
        registros=Count("id"),
    )
    total_horas = float(agg["total_horas"] or 0)
    custo_total = float(agg["soma_custo"] or 0)
    return {
        "custo_total": round(custo_total, 2),
        "total_horas": round(total_horas, 2),
        "custo_medio": (round(custo_total / total_horas, 2) if total_horas else 0),
        "registros": agg["registros"] or 0,
    }


def aggregate_temporal(queryset):
    """Returns monthly time-series list from a technical hours queryset."""
    rows = (
        queryset.annotate(mes=TruncMonth("data"))
        .values("mes")
        .annotate(
            total_horas=Sum("horas_trabalhadas"),
            total_custo=Sum("custo_total"),
        )
        .order_by("mes")
    )
    return [
        {
            "periodo": row["mes"].strftime("%Y-%m"),
            "total_horas": round(float(row["total_horas"] or 0), 2),
            "total_custo": round(float(row["total_custo"] or 0), 2),
        }
        for row in rows
    ]
