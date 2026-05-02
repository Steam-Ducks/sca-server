from django.db.models import (
    DateTimeField,
    ExpressionWrapper,
    F,
    FloatField,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from sca_data.models import (
    GoldBudgetSnapshot,
    SilverComprasProjeto,
    SilverProjeto,
    SilverSolicitacaoCompra,
    SilverTarefaProjeto,
    SilverTempoTarefa,
)


def _build_date_filters(params):
    compras_filter = Q()
    tempo_filter = Q()

    if params.get("start_date"):
        compras_filter &= Q(pedido_compra__data_pedido__gte=params["start_date"])
        tempo_filter &= Q(data__gte=params["start_date"])

    if params.get("end_date"):
        compras_filter &= Q(pedido_compra__data_pedido__lte=params["end_date"])
        tempo_filter &= Q(data__lte=params["end_date"])

    return compras_filter, tempo_filter


def _apply_project_filters(qs, params):
    if params.get("programa"):
        qs = qs.filter(programa__nome_programa__iexact=params["programa"])
    if params.get("projeto"):
        qs = qs.filter(nome_projeto__iexact=params["projeto"])
    if params.get("status"):
        qs = qs.filter(status__iexact=params["status"])
    if params.get("periodo"):
        periodo = params["periodo"]
        qs = qs.filter(
            data_inicio__year=int(periodo[:4]),
            data_inicio__month=int(periodo[5:7]),
        )
    return qs


def _sum_subquery(queryset, group_field, aggregate_expression):
    return Subquery(
        queryset.values(group_field)
        .annotate(total=aggregate_expression)
        .values("total")[:1],
        output_field=FloatField(),
    )


def get_budget_snapshot(params):
    compras_filter, tempo_filter = _build_date_filters(params)

    estimated_materials = _sum_subquery(
        SilverSolicitacaoCompra.objects.filter(projeto=OuterRef("pk")),
        "projeto",
        Coalesce(
            Sum(
                ExpressionWrapper(
                    F("quantidade") * F("material__custo_estimado"),
                    output_field=FloatField(),
                )
            ),
            0.0,
            output_field=FloatField(),
        ),
    )
    estimated_hours = _sum_subquery(
        SilverTarefaProjeto.objects.filter(projeto=OuterRef("pk")),
        "projeto",
        Coalesce(
            Sum(
                ExpressionWrapper(
                    F("estimativa_horas") * F("projeto__custo_hora"),
                    output_field=FloatField(),
                )
            ),
            0.0,
            output_field=FloatField(),
        ),
    )
    actual_materials = _sum_subquery(
        SilverComprasProjeto.objects.filter(projeto=OuterRef("pk")).filter(
            compras_filter
        ),
        "projeto",
        Coalesce(Sum("valor_alocado"), 0.0, output_field=FloatField()),
    )
    actual_hours = _sum_subquery(
        SilverTempoTarefa.objects.filter(tarefa__projeto=OuterRef("pk")).filter(
            tempo_filter
        ),
        "tarefa__projeto",
        Coalesce(
            Sum(
                ExpressionWrapper(
                    F("horas_trabalhadas") * F("tarefa__projeto__custo_hora"),
                    output_field=FloatField(),
                )
            ),
            0.0,
            output_field=FloatField(),
        ),
    )

    qs = _apply_project_filters(
        SilverProjeto.objects.select_related("programa").annotate(
            budget_materiais=Coalesce(estimated_materials, Value(0.0)),
            budget_horas=Coalesce(estimated_hours, Value(0.0)),
            custo_materiais=Coalesce(actual_materials, Value(0.0)),
            custo_horas=Coalesce(actual_hours, Value(0.0)),
        ),
        params,
    )

    rows = []
    for projeto in qs.order_by("nome_projeto"):
        budget = round((projeto.budget_materiais or 0) + (projeto.budget_horas or 0), 2)
        custo_real = round(
            (projeto.custo_materiais or 0) + (projeto.custo_horas or 0), 2
        )
        desvio_percent = round(custo_real / budget * 100, 1) if budget > 0 else 0.0

        if desvio_percent >= 90:
            saude = "Crítico"
        elif desvio_percent >= 70:
            saude = "Atenção"
        else:
            saude = "Saudável"

        projeto.budget = budget
        projeto.desvio_percent = desvio_percent
        projeto.saude_financeira = saude
        projeto.projecao_estouro = (
            round(custo_real - budget, 2) if custo_real > budget else None
        )
        rows.append(projeto)

    saude_filter = params.get("saude")
    if saude_filter:
        rows = [r for r in rows if r.saude_financeira == saude_filter]

    return rows


def get_budget_last_updated_at(params):
    qs = _apply_project_filters(
        SilverProjeto.objects.select_related("programa"),
        params,
    )

    aggregated = qs.aggregate(
        projeto_ingested_at=Max("silver_ingested_at"),
        programa_ingested_at=Max("programa__silver_ingested_at"),
        tarefa_ingested_at=Max("tarefas__silver_ingested_at"),
        tempo_ingested_at=Max(
            "tarefas__tempos__silver_ingested_at",
            output_field=DateTimeField(),
        ),
        solicitacao_ingested_at=Max("silversolicitacaocompra__silver_ingested_at"),
        compra_projeto_ingested_at=Max(
            "silvercomprasprojeto__silver_ingested_at",
            output_field=DateTimeField(),
        ),
        pedido_compra_ingested_at=Max(
            "silvercomprasprojeto__pedido_compra__silver_ingested_at",
            output_field=DateTimeField(),
        ),
    )

    timestamps = [value for value in aggregated.values() if value is not None]
    return max(timestamps) if timestamps else None


def get_budget_snapshot_gold(params):
    qs = GoldBudgetSnapshot.objects.all()
    if params.get("programa"):
        qs = qs.filter(nome_programa__iexact=params["programa"])
    if params.get("projeto"):
        qs = qs.filter(nome_projeto__iexact=params["projeto"])
    if params.get("status"):
        qs = qs.filter(status__iexact=params["status"])
    if params.get("periodo"):
        qs = qs.filter(periodo=params["periodo"])
    if params.get("saude"):
        qs = qs.filter(saude_financeira__iexact=params["saude"])
    return qs.order_by("nome_projeto")


def get_budget_last_updated_at_gold():
    result = GoldBudgetSnapshot.objects.aggregate(latest=Max("gold_updated_at"))
    return result["latest"]
