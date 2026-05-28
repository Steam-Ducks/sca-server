from decimal import ROUND_HALF_UP, Decimal

from django.core.cache import cache
from django.db.models import Avg, Count, Exists, OuterRef, Q, Sum
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response

from materials.selectors import (
    _parse_periodo,
    get_cost_by_project,
    get_filter_options,
    get_materials_queryset,
    get_top_materials_by_financial_impact,
)
from materials.serializers import (
    MaterialsIndicatorsSerializer,
    MaterialsTableSerializer,
    TopMaterialsSerializer,
)
from users.permissions import CanAccessMaterials
from sca_data.models import (
    SilverMaterial,
    SilverPedidoCompra,
    SilverSolicitacaoCompra,
)

_CENTS = Decimal("0.01")
_CACHE_TTL = 300


def _to_brl(value):
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(_CENTS, rounding=ROUND_HALF_UP))


def _ck(prefix, params=None, **kwargs):
    parts = sorted((params or {}).items())
    extra = sorted(kwargs.items())
    suffix = "&".join(f"{k}={v}" for k, v in parts + extra if v)
    return f"{prefix}:{suffix}" if suffix else prefix


class MaterialsTableView(generics.ListAPIView):
    """
    Tabela de pedidos de compra com materiais.


    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    programa    : str        — nome do programa (case-insensitive)
    projeto     : str        — nome do projeto  (case-insensitive)
    material    : str        — descrição do material (contém)
    fornecedor  : str        — razão social do fornecedor (contém)
    categoria   : str        — categoria do material (case-insensitive)

    Prioridade de datas: data_inicio / data_fim > periodo
    """

    serializer_class = MaterialsTableSerializer
    permission_classes = [CanAccessMaterials]

    def get_queryset(self):
        return get_materials_queryset(self.request.query_params)

    def list(self, request, *args, **kwargs):
        key = _ck("materials_table", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, _CACHE_TTL)
        return response


class MaterialsTablePeriodoView(MaterialsTableView):
    """
    Endpoint dedicado para filtro por período no dashboard de materiais.

    Rota: GET /api/compras/periodo/<YYYY-MM>/

    Exemplos
    --------
    GET /api/compras/periodo/2024-03/
    """

    def get_queryset(self):
        raw_periodo = self.kwargs.get("periodo", "")
        primeiro_dia, ultimo_dia = _parse_periodo(raw_periodo)
        params = {
            **self.request.query_params,
            "data_inicio": str(primeiro_dia),
            "data_fim": str(ultimo_dia),
        }
        return get_materials_queryset(params)

    def list(self, request, *args, **kwargs):
        periodo = self.kwargs.get("periodo", "")
        key = _ck("materials_table_p", request.query_params, periodo=periodo)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        # skip MaterialsTableView.list() to avoid double caching
        response = super(MaterialsTableView, self).list(request, *args, **kwargs)
        cache.set(key, response.data, _CACHE_TTL)
        return response


class MaterialsIndicatorsView(generics.GenericAPIView):
    serializer_class = MaterialsIndicatorsSerializer
    permission_classes = [CanAccessMaterials]

    def _build_materiais_queryset(self, params):
        qs = SilverMaterial.objects.filter(status="Ativo")

        if params.get("categoria"):
            qs = qs.filter(categoria__iexact=params["categoria"])

        if params.get("material"):
            qs = qs.filter(descricao__icontains=params["material"])

        # Filters via solicitacoes_compra (projeto / programa)
        sol_q = Q(material_id=OuterRef("pk"))
        apply_sol = False

        if params.get("projeto"):
            sol_q &= Q(projeto__nome_projeto__iexact=params["projeto"])
            apply_sol = True

        if params.get("programa"):
            sol_q &= Q(projeto__programa__nome_programa__iexact=params["programa"])
            apply_sol = True

        if apply_sol:
            qs = qs.filter(Exists(SilverSolicitacaoCompra.objects.filter(sol_q)))

        # Filters via pedidos_compra (fornecedor / periodo)
        ped_q = Q(solicitacao__material_id=OuterRef("pk"))
        apply_ped = False

        if params.get("fornecedor"):
            ped_q &= Q(fornecedor__razao_social__icontains=params["fornecedor"])
            apply_ped = True

        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")
        raw_periodo = params.get("periodo")

        if raw_inicio or raw_fim:
            if raw_inicio:
                ped_q &= Q(data_pedido__gte=raw_inicio)
            if raw_fim:
                ped_q &= Q(data_pedido__lte=raw_fim)
            apply_ped = True
        elif raw_periodo:
            primeiro_dia, ultimo_dia = _parse_periodo(raw_periodo)
            ped_q &= Q(data_pedido__gte=primeiro_dia, data_pedido__lte=ultimo_dia)
            apply_ped = True

        if apply_ped:
            qs = qs.filter(Exists(SilverPedidoCompra.objects.filter(ped_q)))

        return qs

    def get(self, request):
        key = _ck("materials_indicators", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        params = request.query_params
        qs = self._build_materiais_queryset(params)

        agg = qs.aggregate(
            custo_total=Sum("custo_estimado"),
            total_itens=Count("id"),
            custo_medio=Avg("custo_estimado"),
        )

        serializer = self.get_serializer(
            {
                "custo_total": _to_brl(agg["custo_total"]),
                "total_itens": agg["total_itens"],
                "custo_medio": _to_brl(agg["custo_medio"]),
            }
        )
        cache.set(key, serializer.data, _CACHE_TTL)
        return Response(serializer.data)


class TopMaterialsView(APIView):
    """
    Retorna o ranking dos materiais com maior impacto financeiro.


    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    programa    : str
    projeto     : str
    categoria   : str
    fornecedor  : str
    limit       : int        — máximo de itens (padrão: 10)
    """

    permission_classes = [CanAccessMaterials]

    def get(self, request):
        key = _ck("top_materials", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            raise ValidationError({"limit": "O parâmetro limit deve ser um inteiro."})

        data = get_top_materials_by_financial_impact(request.query_params, limit=limit)
        serializer = TopMaterialsSerializer(data, many=True)
        cache.set(key, serializer.data, _CACHE_TTL)
        return Response(serializer.data)


class CostByProjectView(APIView):
    """
    Retorna o custo total de materiais por projeto (ranking do maior para o menor).

    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    programa    : str
    projeto     : str
    categoria   : str
    fornecedor  : str
    """

    permission_classes = [CanAccessMaterials]

    def get(self, request):
        key = _ck("cost_by_project", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        qs = get_cost_by_project(request.query_params)
        data = [
            {"projeto": row["projeto"], "total_cost": float(row["total_cost"] or 0)}
            for row in qs
        ]
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class FilterOptionsView(APIView):
    """
    Retorna os valores disponíveis para cada filtro do painel de materiais.

    A resposta é derivada dos dados reais do banco, garantindo que os dropdowns
    exibam somente períodos, programas, projetos, categorias e fornecedores
    que possuem registros.

    GET /api/materials/filter-options/
    """

    permission_classes = [CanAccessMaterials]

    def get(self, request):
        cached = cache.get("filter_options")
        if cached is not None:
            return Response(cached)
        data = get_filter_options()
        cache.set("filter_options", data, _CACHE_TTL)
        return Response(data)
