import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count, Exists, OuterRef, Q, Sum
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from materials.serializers import (
    MaterialsIndicatorsSerializer,
    MaterialsTableSerializer,
)
from sca_data.models import (
    SilverMaterial,
    SilverPedidoCompra,
    SilverSolicitacaoCompra,
)

_CENTS = Decimal("0.01")


def _to_brl(value):
    if value is None:
        return None
    return float(Decimal(str(value)).quantize(_CENTS, rounding=ROUND_HALF_UP))


class MaterialsTableView(generics.ListAPIView):
    """
    Tabela de pedidos de compra com materiais.

    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo

    Prioridade: data_inicio / data_fim > periodo
    """

    serializer_class = MaterialsTableSerializer

    def _parse_date(self, raw: str, param_name: str) -> datetime.date:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            raise ValidationError(
                {param_name: f"Data inválida '{raw}'. Use o formato YYYY-MM-DD."}
            )

    def _parse_periodo(self, raw: str) -> tuple:
        """YYYY-MM → (primeiro_dia, último_dia) do mês."""
        try:
            if len(raw) != 7 or raw[4] != "-":
                raise ValueError
            year, month = int(raw[:4]), int(raw[5:7])
            if not (1 <= month <= 12):
                raise ValueError
        except (ValueError, IndexError):
            raise ValidationError(
                {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
            )

        primeiro_dia = datetime.date(year, month, 1)
        if month == 12:
            ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        return primeiro_dia, ultimo_dia

    def _filters_from_date_range(self, raw_inicio, raw_fim) -> dict:
        filters = {}
        if raw_inicio:
            filters["data_pedido__gte"] = self._parse_date(raw_inicio, "data_inicio")
        if raw_fim:
            filters["data_pedido__lte"] = self._parse_date(raw_fim, "data_fim")
        if (
            raw_inicio
            and raw_fim
            and filters["data_pedido__gte"] > filters["data_pedido__lte"]
        ):
            raise ValidationError(
                {"data_inicio": "data_inicio não pode ser posterior a data_fim."}
            )
        return filters

    def _build_period_filters(self) -> dict:
        params = self.request.query_params
        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")
        raw_periodo = params.get("periodo")

        if raw_inicio or raw_fim:
            return self._filters_from_date_range(raw_inicio, raw_fim)

        if raw_periodo:
            primeiro_dia, ultimo_dia = self._parse_periodo(raw_periodo)
            return {"data_pedido__gte": primeiro_dia, "data_pedido__lte": ultimo_dia}

        return {}

    def get_queryset(self):
        filters = self._build_period_filters()

        return (
            SilverPedidoCompra.objects.select_related(
                "solicitacao__material",
                "solicitacao__projeto__programa",
                "fornecedor",
            )
            .filter(solicitacao__isnull=False)
            .filter(**filters)
            .order_by("-valor_total")
        )


class MaterialsTablePeriodoView(MaterialsTableView):
    """
    Endpoint dedicado para filtro por período no dashboard de materiais.

    Rota: GET /api/compras/periodo/<YYYY-MM>/

    Exemplos
    --------
    GET /api/compras/periodo/2024-03/
    """

    def _build_period_filters(self) -> dict:
        raw_periodo = self.kwargs.get("periodo", "")
        primeiro_dia, ultimo_dia = self._parse_periodo(raw_periodo)
        return {
            "data_pedido__gte": primeiro_dia,
            "data_pedido__lte": ultimo_dia,
        }


class MaterialsIndicatorsView(generics.GenericAPIView):
    serializer_class = MaterialsIndicatorsSerializer

    def _parse_periodo(self, raw: str) -> tuple:
        try:
            if len(raw) != 7 or raw[4] != "-":
                raise ValueError
            year, month = int(raw[:4]), int(raw[5:7])
            if not (1 <= month <= 12):
                raise ValueError
        except (ValueError, IndexError):
            raise ValidationError(
                {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
            )
        primeiro_dia = datetime.date(year, month, 1)
        if month == 12:
            ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        return primeiro_dia, ultimo_dia

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

        raw_periodo = params.get("periodo")
        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")

        if raw_inicio or raw_fim:
            if raw_inicio:
                ped_q &= Q(data_pedido__gte=raw_inicio)
            if raw_fim:
                ped_q &= Q(data_pedido__lte=raw_fim)
            apply_ped = True
        elif raw_periodo:
            primeiro_dia, ultimo_dia = self._parse_periodo(raw_periodo)
            ped_q &= Q(data_pedido__gte=primeiro_dia, data_pedido__lte=ultimo_dia)
            apply_ped = True

        if apply_ped:
            qs = qs.filter(Exists(SilverPedidoCompra.objects.filter(ped_q)))

        return qs

    def get(self, request):
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
        return Response(serializer.data)
