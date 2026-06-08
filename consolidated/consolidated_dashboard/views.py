import datetime

from django.core.cache import cache
from django.db.models import ExpressionWrapper, F, FloatField, Max, Q, Sum
from django.utils import timezone

from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from consolidated.consolidated_dashboard.serializers import (
    ConsolidatedDashboardSerializer,
)
from sca_data.models import SilverProjeto
from users.permissions import CanAccessConsolidated
from core.utils.date_utils import parse_date, parse_period

_CACHE_TTL = 300


def _ck(prefix, params=None, **kwargs):
    parts = sorted((params or {}).items())
    extra = sorted(kwargs.items())
    suffix = "&".join(f"{k}={v}" for k, v in parts + extra if v)
    return f"{prefix}:{suffix}" if suffix else prefix


class ConsolidatedDashboardView(generics.ListAPIView):
    permission_classes = [CanAccessConsolidated]
    """
    Tabela consolidada por projeto - une custos de materiais e horas tecnicas.

    Query params
    ------------
    periodo     : YYYY-MM    - mes completo (data_pedido e data de horas)
    data_inicio : YYYY-MM-DD - bound inferior inclusivo
    data_fim    : YYYY-MM-DD - bound superior inclusivo
    programa    : str        - filtra pelo nome do programa
    projeto     : str        - filtra pelo nome do projeto
    status      : str        - filtra pelo status do projeto

    Prioridade: data_inicio / data_fim > periodo

    Mapeamento de related_names (models.py):
      SilverProjeto -> SilverTarefaProjeto       : tarefas
      SilverTarefaProjeto -> SilverTempoTarefa   : tempos
      SilverProjeto -> SilverComprasProjeto      : silvercomprasprojeto (default)
      SilverComprasProjeto -> SilverPedidoCompra : pedido_compra (FK field name)
      SilverProjeto -> SilverSolicitacaoCompra   : silversolicitacaocompra (query name)
    """

    serializer_class = ConsolidatedDashboardSerializer

    def _get_date_range(self) -> tuple:
        params = self.request.query_params

        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")
        raw_periodo = params.get("periodo")

        if raw_inicio or raw_fim:
            data_inicio = parse_date(raw_inicio, "data_inicio") if raw_inicio else None
            data_fim = parse_date(raw_fim, "data_fim") if raw_fim else None

            if data_inicio and data_fim and data_inicio > data_fim:
                raise DRFValidationError(
                    {"data_inicio": "data_inicio nao pode ser posterior a data_fim."}
                )

            return data_inicio, data_fim

        if raw_periodo:
            return parse_period(raw_periodo)

        return None, None

    def _apply_filters(self, qs, params=None):
        if params is None:
            params = {}

        programa = params.get("programa")
        projeto = params.get("projeto")
        status = params.get("status")

        if programa:
            qs = qs.filter(programa__nome_programa__iexact=programa)
        if projeto:
            qs = qs.filter(nome_projeto__iexact=projeto)
        if status:
            qs = qs.filter(status__iexact=status)

        return qs

    def _build_source_filters(self, data_inicio=None, data_fim=None):
        compras_filter = Q()
        tempo_filter = Q()

        if data_inicio:
            compras_filter &= Q(
                silvercomprasprojeto__pedido_compra__data_pedido__gte=data_inicio
            )
            tempo_filter &= Q(tarefas__tempos__data__gte=data_inicio)
        if data_fim:
            compras_filter &= Q(
                silvercomprasprojeto__pedido_compra__data_pedido__lte=data_fim
            )
            tempo_filter &= Q(tarefas__tempos__data__lte=data_fim)

        return compras_filter, tempo_filter

    def _build_queryset(self, data_inicio=None, data_fim=None, params=None):
        compras_filter, tempo_filter = self._build_source_filters(
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        qs = SilverProjeto.objects.select_related("programa").annotate(
            custo_materiais=Sum(
                "silvercomprasprojeto__valor_alocado",
                filter=compras_filter,
            ),
            custo_horas=Sum(
                ExpressionWrapper(
                    F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                    output_field=FloatField(),
                ),
                filter=tempo_filter,
            ),
            qtd_materiais=Sum("silversolicitacaocompra__quantidade"),
            total_horas=Sum(
                "tarefas__tempos__horas_trabalhadas",
                filter=tempo_filter,
            ),
        )

        qs = self._apply_filters(qs, params=params)
        return qs.order_by(F("custo_materiais").desc(nulls_last=True))

    def _get_last_updated_at(self, data_inicio=None, data_fim=None, params=None):
        compras_filter, tempo_filter = self._build_source_filters(
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        qs = self._apply_filters(
            SilverProjeto.objects.select_related("programa"),
            params=params,
        )

        aggregated = qs.aggregate(
            projeto_ingested_at=Max("silver_ingested_at"),
            programa_ingested_at=Max("programa__silver_ingested_at"),
            tarefa_ingested_at=Max("tarefas__silver_ingested_at"),
            tempo_ingested_at=Max(
                "tarefas__tempos__silver_ingested_at",
                filter=tempo_filter,
            ),
            solicitacao_ingested_at=Max("silversolicitacaocompra__silver_ingested_at"),
            compra_projeto_ingested_at=Max(
                "silvercomprasprojeto__silver_ingested_at",
                filter=compras_filter,
            ),
            pedido_compra_ingested_at=Max(
                "silvercomprasprojeto__pedido_compra__silver_ingested_at",
                filter=compras_filter,
            ),
        )

        timestamps = [value for value in aggregated.values() if value is not None]

        if not timestamps:
            return None

        normalized = []
        for ts in timestamps:
            if timezone.is_naive(ts):
                normalized.append(ts.replace(tzinfo=datetime.timezone.utc))
            else:
                normalized.append(ts)

        return max(normalized)

    def get_queryset(self):
        data_inicio, data_fim = self._get_date_range()
        return self._build_queryset(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=self.request.query_params,
        )

    def list(self, request, *args, **kwargs):
        key = _ck("consolidated", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data_inicio, data_fim = self._get_date_range()
        last_updated_at = self._get_last_updated_at(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=request.query_params,
        )
        data = {
            "data": serializer.data,
            "last_updated_at": (
                last_updated_at.isoformat() if last_updated_at else None
            ),
        }
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class ConsolidatedDashboardPeriodoView(ConsolidatedDashboardView):
    """
    Endpoint dedicado para filtro por periodo no dashboard consolidado.

    Rota: GET /api/consolidated/periodo/<YYYY-MM>/

    Herda _build_queryset e usa parse_period para resolver o intervalo.

    Exemplos
    --------
    GET /api/consolidated/periodo/2024-03/
    GET /api/consolidated/periodo/2024-03/?programa=Cloud
    GET /api/consolidated/periodo/2024-03/?status=Em Andamento
    """

    def get_queryset(self):
        raw_periodo = self.kwargs.get("periodo", "")
        data_inicio, data_fim = parse_period(raw_periodo)
        return self._build_queryset(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=self.request.query_params,
        )

    def list(self, request, *args, **kwargs):
        periodo = self.kwargs.get("periodo", "")
        key = _ck("consolidated_p", request.query_params, periodo=periodo)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        data_inicio, data_fim = parse_period(periodo)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        last_updated_at = self._get_last_updated_at(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=request.query_params,
        )
        data = {
            "data": serializer.data,
            "last_updated_at": (
                last_updated_at.isoformat() if last_updated_at else None
            ),
        }
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
