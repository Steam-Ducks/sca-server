import datetime

from django.db.models import Count, ExpressionWrapper, F, FloatField, Sum
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from sca_data.models import SilverTempoTarefa
from technical_hours.serializers import TechnicalHoursTableSerializer


class TechnicalHoursTableView(generics.ListAPIView):
    """
    Tabela de horas técnicas por colaborador.

    Query params
    ------------
    periodo     : YYYY-MM    — mês completo
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    ano         : int        — filtra pelo ano
    mes         : int        — filtra pelo mês

    Prioridade: data_inicio / data_fim > periodo > ano / mes
    """

    serializer_class = TechnicalHoursTableSerializer

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
            filters["data__gte"] = self._parse_date(raw_inicio, "data_inicio")
        if raw_fim:
            filters["data__lte"] = self._parse_date(raw_fim, "data_fim")
        if raw_inicio and raw_fim and filters["data__gte"] > filters["data__lte"]:
            raise ValidationError(
                {"data_inicio": "data_inicio não pode ser posterior a data_fim."}
            )
        return filters

    def _filters_from_ano_mes(self, ano, mes) -> dict:
        filters = {}
        if ano:
            try:
                filters["data__year"] = int(ano)
            except ValueError:
                raise ValidationError({"ano": "Deve ser um número inteiro."})
        if mes:
            try:
                filters["data__month"] = int(mes)
            except ValueError:
                raise ValidationError({"mes": "Deve ser um número inteiro."})
        return filters

    def _build_period_filters(self):
        params = self.request.query_params
        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")
        raw_periodo = params.get("periodo")

        if raw_inicio or raw_fim:
            return self._filters_from_date_range(raw_inicio, raw_fim)

        if raw_periodo:
            primeiro_dia, ultimo_dia = self._parse_periodo(raw_periodo)
            return {"data__gte": primeiro_dia, "data__lte": ultimo_dia}

        return self._filters_from_ano_mes(params.get("ano"), params.get("mes"))

    def get_queryset(self):
        filters = self._build_period_filters()

        return (
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
            .order_by("-custo_total")
        )


class TechnicalHoursKpiView(TechnicalHoursTableView):
    """
    Indicadores agregados de horas técnicas.

    Rota: GET /api/horas-tecnicas/kpis/

    Aceita os mesmos query params de TechnicalHoursTableView:
    periodo, data_inicio, data_fim, ano, mes.

    Retorna
    -------
    custo_total  : soma do custo total de horas
    total_horas  : soma de horas trabalhadas
    custo_medio  : custo_total / total_horas
    registros    : número de registros
    """

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        agg = qs.aggregate(
            total_horas=Sum("horas_trabalhadas"),
            soma_custo=Sum("custo_total"),
            registros=Count("id"),
        )
        total_horas = float(agg["total_horas"] or 0)
        custo_total = float(agg["soma_custo"] or 0)
        return Response(
            {
                "custo_total": round(custo_total, 2),
                "total_horas": round(total_horas, 2),
                "custo_medio": round(custo_total / total_horas, 2) if total_horas else 0,
                "registros": agg["registros"] or 0,
            }
        )


class TechnicalHoursTablePeriodoView(TechnicalHoursTableView):
    """
    Endpoint dedicado para filtro por período no dashboard de horas técnicas.

    Rota: GET /api/horas-tecnicas/periodo/<YYYY-MM>/

    Herda _parse_periodo de TechnicalHoursTableView.

    Exemplos
    --------
    GET /api/horas-tecnicas/periodo/2024-03/
    GET /api/horas-tecnicas/periodo/2024-03/?ano=2024
    """

    def _build_period_filters(self):
        raw_periodo = self.kwargs.get("periodo", "")
        primeiro_dia, ultimo_dia = self._parse_periodo(raw_periodo)
        return {
            "data__gte": primeiro_dia,
            "data__lte": ultimo_dia,
        }
