from django.db.models import Count, ExpressionWrapper, F, FloatField, Q, Sum
from django.db.models.functions import Coalesce

from sca_data.models import SilverProjeto


def get_projects_by_period(start_date=None, end_date=None):
    """
    Filter projects by a given date range using silver_ingested_at.
    """

    date_filter = Q()

    if start_date:
        date_filter &= Q(silver_ingested_at__date__gte=start_date)

    if end_date:
        date_filter &= Q(silver_ingested_at__date__lte=end_date)

    return SilverProjeto.objects.filter(date_filter)


def get_program_summary(params):
    """
    Returns aggregated cost data grouped by program.

    Accepted params:
        start_date — YYYY-MM-DD  (filters pedido_compra.data_pedido and tempo_tarefa.data)
        end_date   — YYYY-MM-DD
        programa   — program name (case-insensitive)
        projeto    — project name (case-insensitive)

    Returns a list of dicts sorted by custo_materiais descending.
    """
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    programa = params.get("programa")
    projeto = params.get("projeto")

    compras_filter = Q()
    tempo_filter = Q()

    if start_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__gte=start_date
        )
        tempo_filter &= Q(tarefas__tempos__data__gte=start_date)

    if end_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__lte=end_date
        )
        tempo_filter &= Q(tarefas__tempos__data__lte=end_date)

    qs = SilverProjeto.objects.select_related("programa")

    if programa:
        qs = qs.filter(programa__nome_programa__iexact=programa)

    if projeto:
        qs = qs.filter(nome_projeto__iexact=projeto)

    rows = (
        qs.values("programa__nome_programa")
        .annotate(
            qtd_projetos=Count("id", distinct=True),
            custo_materiais=Coalesce(
                Sum("silvercomprasprojeto__valor_alocado", filter=compras_filter),
                0.0,
                output_field=FloatField(),
            ),
            custo_horas=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                        output_field=FloatField(),
                    ),
                    filter=tempo_filter,
                ),
                0.0,
                output_field=FloatField(),
            ),
        )
        .order_by("-custo_materiais")
    )

    return [
        {
            "programa": row["programa__nome_programa"] or "Sem Programa",
            "qtd_projetos": row["qtd_projetos"],
            "custo_materiais": round(row["custo_materiais"], 2),
            "custo_horas": round(row["custo_horas"], 2),
            "custo_total": round(row["custo_materiais"] + row["custo_horas"], 2),
        }
        for row in rows
    ]


def _build_cost_filters(params):
    """Shared helper: builds Q filters for materials and hours from params dict."""
    start_date = params.get("start_date")
    end_date = params.get("end_date")

    compras_filter = Q()
    tempo_filter = Q()

    if start_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__gte=start_date
        )
        tempo_filter &= Q(tarefas__tempos__data__gte=start_date)

    if end_date:
        compras_filter &= Q(
            silvercomprasprojeto__pedido_compra__data_pedido__lte=end_date
        )
        tempo_filter &= Q(tarefas__tempos__data__lte=end_date)

    return compras_filter, tempo_filter


def get_cost_composition(params):
    """
    Returns the overall cost composition split between materials and hours.

    Accepted params:
        start_date — YYYY-MM-DD
        end_date   — YYYY-MM-DD
        programa   — program name (case-insensitive)
        projeto    — project name (case-insensitive)

    Returns a dict with absolute values and percentage breakdown.
    """
    compras_filter, tempo_filter = _build_cost_filters(params)

    qs = SilverProjeto.objects.select_related("programa")

    if params.get("programa"):
        qs = qs.filter(programa__nome_programa__iexact=params["programa"])
    if params.get("projeto"):
        qs = qs.filter(nome_projeto__iexact=params["projeto"])

    result = qs.aggregate(
        custo_materiais=Coalesce(
            Sum("silvercomprasprojeto__valor_alocado", filter=compras_filter),
            0.0,
            output_field=FloatField(),
        ),
        custo_horas=Coalesce(
            Sum(
                ExpressionWrapper(
                    F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                    output_field=FloatField(),
                ),
                filter=tempo_filter,
            ),
            0.0,
            output_field=FloatField(),
        ),
    )

    custo_materiais = round(result["custo_materiais"], 2)
    custo_horas = round(result["custo_horas"], 2)
    custo_total = round(custo_materiais + custo_horas, 2)

    if custo_total > 0:
        pct_materiais = round(custo_materiais / custo_total * 100, 1)
        pct_horas = round(custo_horas / custo_total * 100, 1)
    else:
        pct_materiais = 0.0
        pct_horas = 0.0

    return {
        "custo_materiais": custo_materiais,
        "custo_horas": custo_horas,
        "custo_total": custo_total,
        "pct_materiais": pct_materiais,
        "pct_horas": pct_horas,
    }
