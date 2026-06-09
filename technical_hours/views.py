from django.core.cache import cache
from django.db.models import Count, ExpressionWrapper, F, FloatField, Sum
from django.db.models.functions import TruncMonth
from rest_framework.response import Response

from core.views import BaseFilteredListView
from sca_data.models import SilverTempoTarefa
from technical_hours.serializers import TechnicalHoursTableSerializer
from users.permissions import CanAccessTechnicalHours
from core.utils.filters import build_date_filters

_CACHE_TTL = 300


def _ck(prefix, params=None, **kwargs):
    parts = sorted((params or {}).items())
    extra = sorted(kwargs.items())
    suffix = "&".join(f"{k}={v}" for k, v in parts + extra if v)
    return f"{prefix}:{suffix}" if suffix else prefix


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

    def _apply_dimension_filters(self, queryset):
        params = self.request.query_params

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

        return queryset

    def get_queryset(self):
        filters = self._build_period_filters()

        queryset = (
            SilverTempoTarefa.objects.select_related("tarefa__projeto__programa")
            .filter(tarefa__isnull=False)
            .filter(**filters)
            .annotate(
                custo_por_hora=F("tarefa__projeto__custo_hora"),
                custo_total=ExpressionWrapper(
                    F("horas_trabalhadas") * F("tarefa__projeto__custo_hora"),
                    output_field=FloatField(),
                ),
            )
        )
        queryset = self._apply_dimension_filters(queryset)
        return queryset.order_by("-custo_total")


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

    def get(self, request, *args, **kwargs):
        key = _ck("tech_hours_kpi", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        qs = self.get_queryset()
        agg = qs.aggregate(
            total_horas=Sum("horas_trabalhadas"),
            soma_custo=Sum("custo_total"),
            registros=Count("id"),
        )
        total_horas = float(agg["total_horas"] or 0)
        custo_total = float(agg["soma_custo"] or 0)
        data = {
            "custo_total": round(custo_total, 2),
            "total_horas": round(total_horas, 2),
            "custo_medio": (round(custo_total / total_horas, 2) if total_horas else 0),
            "registros": agg["registros"] or 0,
        }
        cache.set(key, data, _CACHE_TTL)
        return Response(data)


class TechnicalHoursTablePeriodoView(TechnicalHoursTableView):
    """
    Endpoint dedicado para filtro por período no dashboard de horas técnicas.

    Rota: GET /api/horas-tecnicas/periodo/<YYYY-MM>/

    Usa build_date_filters para resolver o intervalo do periodo.

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

    def _build_period_filters(self):
        return {}

    def get(self, request, *args, **kwargs):
        key = _ck("tech_hours_temporal", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        qs = self.get_queryset()
        agg = (
            qs.annotate(mes=TruncMonth("data"))
            .values("mes")
            .annotate(
                total_horas=Sum("horas_trabalhadas"),
                total_custo=Sum("custo_total"),
            )
            .order_by("mes")
        )
        data = [
            {
                "periodo": row["mes"].strftime("%Y-%m"),
                "total_horas": round(float(row["total_horas"] or 0), 2),
                "total_custo": round(float(row["total_custo"] or 0), 2),
            }
            for row in agg
        ]
        cache.set(key, data, _CACHE_TTL)
        return Response(data)
