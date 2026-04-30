import datetime

from django.db.models import Q
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.db.models import Sum, F
from sca_data.models import SilverPedidoCompra
from django.db.models import DecimalField
from django.db.models.functions import Cast


def _parse_date(raw: str, param_name: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        raise DRFValidationError(
            {param_name: f"Data inválida '{raw}'. Use o formato YYYY-MM-DD."}
        )


def _parse_periodo(raw: str) -> tuple:
    """YYYY-MM → (primeiro_dia, último_dia) do mês."""
    try:
        if len(raw) != 7 or raw[4] != "-":
            raise ValueError
        year, month = int(raw[:4]), int(raw[5:7])
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, IndexError):
        raise DRFValidationError(
            {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
        )

    primeiro_dia = datetime.date(year, month, 1)
    if month == 12:
        ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

    return primeiro_dia, ultimo_dia


def _get_date_range(params) -> tuple:
    """
    Resolve o intervalo de datas a partir dos query params.

    Prioridade: data_inicio / data_fim > periodo
    """
    raw_inicio = params.get("data_inicio")
    raw_fim = params.get("data_fim")
    raw_periodo = params.get("periodo")

    if raw_inicio or raw_fim:
        data_inicio = _parse_date(raw_inicio, "data_inicio") if raw_inicio else None
        data_fim = _parse_date(raw_fim, "data_fim") if raw_fim else None

        if data_inicio and data_fim and data_inicio > data_fim:
            raise DRFValidationError(
                {"data_inicio": "data_inicio não pode ser posterior a data_fim."}
            )

        return data_inicio, data_fim

    if raw_periodo:
        return _parse_periodo(raw_periodo)

    return None, None


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
    data_inicio, data_fim = _get_date_range(params)

    filters = Q(solicitacao__isnull=False)

    # --- Período ---
    if data_inicio:
        filters &= Q(data_pedido__gte=data_inicio)
    if data_fim:
        filters &= Q(data_pedido__lte=data_fim)

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
