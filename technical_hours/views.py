from django.core.cache import cache
from rest_framework.response import Response

from core.utils.filters import build_date_filters
from core.views import BaseFilteredListView
from technical_hours.selectors import (
    aggregate_kpis,
    aggregate_temporal,
    get_technical_hours_queryset,
)
from technical_hours.serializers import TechnicalHoursTableSerializer
from users.permissions import CanAccessTechnicalHours

_CACHE_TTL = 300


class TechnicalHoursTableView(BaseFilteredListView):
    """
    Tabela de horas técnicas por colaborador.

    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    ano         : int        — filtra pelo ano
    mes         : int        — filtra pelo mês
    programa    : str        — filtra pelo nome do programa
    projeto     : str        — filtra pelo nome do projeto

    Prioridade: data_inicio / data_fim > periodo > ano / mes
    """

    serializer_class = TechnicalHoursTableSerializer
    permission_classes = [CanAccessTechnicalHours]
    cache_key_prefix = "tech_hours_table"

    def _build_period_filters(self):
        return build_date_filters(
            self.request.query_params,
            field="data",
            allow_year_month=True,
        )

    def get_queryset(self):
        return get_technical_hours_queryset(
            self.request.query_params,
            period_filters=self._build_period_filters(),
        )


class TechnicalHoursKpiView(TechnicalHoursTableView):
    """
    Indicadores agregados de horas técnicas.

    Rota: GET /api/horas-tecnicas/kpis/

    Aceita os mesmos query params de TechnicalHoursTableView:
    periodo, data_inicio, data_fim, ano, mes, programa, projeto.

    Retorna
    -------
    custo_total  : soma do custo total de horas
    total_horas  : soma de horas trabalhadas
    custo_medio  : custo_total / total_horas
    registros    : número de registros
    """

    cache_key_prefix = "tech_hours_kpi"

    def get(self, request, *args, **kwargs):
        key = self.get_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        data = aggregate_kpis(self.get_queryset())
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class TechnicalHoursTablePeriodoView(TechnicalHoursTableView):
    """
    Endpoint dedicado para filtro por período no dashboard de horas técnicas.

    Rota: GET /api/horas-tecnicas/periodo/<YYYY-MM>/

    Exemplos
    --------
    GET /api/horas-tecnicas/periodo/2024-03/
    GET /api/horas-tecnicas/periodo/2024-03/?ano=2024
    """

    cache_key_prefix = "tech_hours_table_p"

    def get_cache_key_extra(self):
        return {"periodo": self.kwargs.get("periodo", "")}

    def _build_period_filters(self):
        raw_periodo = self.kwargs.get("periodo", "")
        return build_date_filters({"periodo": raw_periodo}, field="data")


class TechnicalHoursTemporalView(TechnicalHoursTableView):
    """
    Evolução temporal de horas — total de horas por período.

    Rota: GET /api/horas-tecnicas/temporal/

    Aceita os filtros de dimensão (programa, projeto) mas ignora filtros
    de período para expor a série histórica completa.

    Retorna
    -------
    lista de {"periodo": "YYYY-MM", "total_horas": float, "total_custo": float}
    ordenada cronologicamente.
    """

    cache_key_prefix = "tech_hours_temporal"

    def _build_period_filters(self):
        return {}

    def get(self, request, *args, **kwargs):
        key = self.get_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        data = aggregate_temporal(self.get_queryset())
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
