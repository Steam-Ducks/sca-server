from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Cast, TruncMonth
from core.utils.filters import build_date_filters
from sca_data.models import SilverPedidoCompra


def get_materials_queryset(params):
    """
    Retorna o queryset de SilverPedidoCompra com os filtros aplicados.

    Query params aceitos
    --------------------
    periodo       : YYYY-MM   — mês completo (mapeia data_pedido)
    data_inicio   : YYYY-MM-DD — limite inferior inclusivo de data_pedido
    data_fim      : YYYY-MM-DD — limite superior inclusivo de data_pedido
    programa      : str        — nome_programa (case-insensitive)
    projeto       : str        — nome_projeto  (case-insensitive)
    material      : str        — descricao do material (case-insensitive, contains)
    fornecedor    : str        — razao_social do fornecedor (case-insensitive, contains)
    categoria     : str        — categoria do material (case-insensitive)

    Prioridade de datas: data_inicio / data_fim > periodo
    """
    filters = Q(solicitacao__isnull=False)
    filters &= Q(**build_date_filters(params, field="data_pedido"))

    # --- Programa ---
    programa = params.get("programa")
    if programa:
        filters &= Q(solicitacao__projeto__programa__nome_programa__iexact=programa)

    # --- Projeto ---
    projeto = params.get("projeto")
    if projeto:
        filters &= Q(solicitacao__projeto__nome_projeto__iexact=projeto)

    # --- Material ---
    material = params.get("material")
    if material:
        filters &= Q(solicitacao__material__descricao__icontains=material)

    # --- Fornecedor ---
    fornecedor = params.get("fornecedor")
    if fornecedor:
        filters &= Q(fornecedor__razao_social__icontains=fornecedor)

    # --- Categoria ---
    categoria = params.get("categoria")
    if categoria:
        filters &= Q(solicitacao__material__categoria__iexact=categoria)

    return (
        SilverPedidoCompra.objects.select_related(
            "solicitacao__material",
            "solicitacao__projeto__programa",
            "fornecedor",
        )
        .filter(filters)
        .order_by("-valor_total")
    )


# Retorna os materiais com maior impacto financeiro (top N por custo total)
def get_top_materials_by_financial_impact(params, limit=10):
    base_qs = get_materials_queryset(params)

    return (
        base_qs.values("solicitacao__material__descricao")
        .annotate(
            material=F("solicitacao__material__descricao"),
            total_cost=Sum("valor_total"),
        )
        .values("material", "total_cost")
        .order_by("-total_cost")[:limit]
    )


# Calcula o custo total de materiais por projeto (ranking do maior para o menor)
def get_cost_by_project(params, limit=None):
    base_qs = get_materials_queryset(params)

    qs = (
        base_qs.values("solicitacao__projeto__nome_projeto")
        .annotate(
            projeto=F("solicitacao__projeto__nome_projeto"),
            total_cost=Cast(
                Sum("valor_total"),
                DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .values("projeto", "total_cost")
        .order_by("-total_cost")
    )

    if limit:
        qs = qs[:limit]

    return qs


def get_filter_options() -> dict:
    """
    Retorna os valores disponíveis para cada filtro baseados nos dados reais do banco.

    Todas as queries partem de SilverPedidoCompra com solicitacao__isnull=False,
    garantindo que os valores exibidos nos dropdowns correspondam exatamente ao
    conjunto de dados que as queries de filtro retornam.
    """
    base_qs = SilverPedidoCompra.objects.filter(solicitacao__isnull=False)

    # Períodos: meses distintos de data_pedido, ordenados do mais recente ao mais antigo
    meses_qs = (
        base_qs.filter(data_pedido__isnull=False)
        .annotate(mes=TruncMonth("data_pedido"))
        .values_list("mes", flat=True)
        .distinct()
        .order_by("-mes")
    )
    periodos = sorted(
        {m.strftime("%Y-%m") for m in meses_qs if m},
        reverse=True,
    )

    # Programas que têm pelo menos um pedido real
    programas = list(
        base_qs.filter(solicitacao__projeto__programa__nome_programa__isnull=False)
        .exclude(solicitacao__projeto__programa__nome_programa="")
        .values_list("solicitacao__projeto__programa__nome_programa", flat=True)
        .distinct()
        .order_by("solicitacao__projeto__programa__nome_programa")
    )

    # Projetos com programa associado — permite filtro cruzado no frontend
    projetos_qs = (
        base_qs.filter(solicitacao__projeto__nome_projeto__isnull=False)
        .exclude(solicitacao__projeto__nome_projeto="")
        .values(
            "solicitacao__projeto__nome_projeto",
            "solicitacao__projeto__programa__nome_programa",
        )
        .distinct()
        .order_by("solicitacao__projeto__nome_projeto")
    )
    projetos = [
        {
            "nome": p["solicitacao__projeto__nome_projeto"],
            "programa": p["solicitacao__projeto__programa__nome_programa"],
        }
        for p in projetos_qs
    ]

    # Categorias de materiais presentes em pedidos reais
    categorias = list(
        base_qs.filter(solicitacao__material__categoria__isnull=False)
        .exclude(solicitacao__material__categoria="")
        .values_list("solicitacao__material__categoria", flat=True)
        .distinct()
        .order_by("solicitacao__material__categoria")
    )

    # Fornecedores de pedidos reais (sem reverse relation)
    fornecedores = list(
        base_qs.filter(fornecedor__razao_social__isnull=False)
        .exclude(fornecedor__razao_social="")
        .values_list("fornecedor__razao_social", flat=True)
        .distinct()
        .order_by("fornecedor__razao_social")
    )

    return {
        "periodos": periodos,
        "programas": programas,
        "projetos": projetos,
        "categorias": categorias,
        "fornecedores": fornecedores,
    }
