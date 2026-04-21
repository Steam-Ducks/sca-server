import datetime

from django.db.models import F, FloatField, ExpressionWrapper, Sum, Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError

from sca_data.models import SilverProjeto
from consolidated.consolidated_dashboard.serializers import (
    ConsolidatedDashboardSerializer,
)


class ConsolidatedDashboardView(generics.ListAPIView):
    """
    Tabela consolidada por projeto — une custos de materiais e horas técnicas.

    Query params
    ------------
    periodo     : YYYY-MM   — mês completo (data_pedido e data de horas)
    data_inicio : YYYY-MM-DD — bound inferior inclusivo
    data_fim    : YYYY-MM-DD — bound superior inclusivo
    programa    : str        — filtra pelo nome do programa
    projeto     : str        — filtra pelo nome do projeto
    status      : str        — filtra pelo status do projeto

    Prioridade: data_inicio / data_fim > periodo

    Mapeamento de related_names (models.py):
      SilverProjeto → SilverTarefaProjeto        : tarefas
      SilverTarefaProjeto → SilverTempoTarefa    : tempos
      SilverProjeto → SilverComprasProjeto       : silvercomprasprojeto (default)
      SilverComprasProjeto → SilverPedidoCompra  : pedido_compra (FK field name)
      SilverProjeto → SilverSolicitacaoCompra    : silversolicitacaocompra_set (default)
    """

    serializer_class = ConsolidatedDashboardSerializer

    def _parse_date(self, raw: str, param_name: str) -> datetime.date:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            raise DRFValidationError(
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
            raise DRFValidationError(
                {"periodo": f"Período inválido '{raw}'. Use o formato YYYY-MM."}
            )

        primeiro_dia = datetime.date(year, month, 1)
        if month == 12:
            ultimo_dia = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            ultimo_dia = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        return primeiro_dia, ultimo_dia

    def _get_date_range(self) -> tuple:
        params = self.request.query_params

        raw_inicio = params.get("data_inicio")
        raw_fim = params.get("data_fim")
        raw_periodo = params.get("periodo")

        if raw_inicio or raw_fim:
            data_inicio = (
                self._parse_date(raw_inicio, "data_inicio") if raw_inicio else None
            )
            data_fim = self._parse_date(raw_fim, "data_fim") if raw_fim else None

            if data_inicio and data_fim and data_inicio > data_fim:
                raise DRFValidationError(
                    {"data_inicio": "data_inicio não pode ser posterior a data_fim."}
                )

            return data_inicio, data_fim

        if raw_periodo:
            return self._parse_periodo(raw_periodo)

        return None, None

    def _build_queryset(self, data_inicio=None, data_fim=None, params=None):
        """
        Monta o queryset anotado com filtros de data e query params opcionais.

        Relacionamentos usados (conforme models.py):
          - tarefas → tempos          (horas trabalhadas)
          - silvercomprasprojeto → pedido_compra  (custo materiais via SilverComprasProjeto)
          - silversolicitacaocompra_set            (qtd materiais)
        """
        if params is None:
            params = {}

        # Filtro de datas para pedidos (via SilverComprasProjeto → SilverPedidoCompra)
        compras_filter = Q()
        # Filtro de datas para horas (via SilverTarefaProjeto → SilverTempoTarefa)
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

        qs = SilverProjeto.objects.select_related("programa").annotate(
            # Custo materiais: soma do valor_alocado por projeto em SilverComprasProjeto
            custo_materiais=Sum(
                "silvercomprasprojeto__valor_alocado",
                filter=compras_filter,
            ),
            # Custo horas: soma de horas_trabalhadas * custo_hora do projeto
            custo_horas=Sum(
                ExpressionWrapper(
                    F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                    output_field=FloatField(),
                ),
                filter=tempo_filter,
            ),
            # Qtd materiais: soma das quantidades das solicitações de compra
            qtd_materiais=Sum(
                "silversolicitacaocompra__quantidade",
            ),
            # Total horas trabalhadas
            total_horas=Sum(
                "tarefas__tempos__horas_trabalhadas",
                filter=tempo_filter,
            ),
        )

        programa = params.get("programa")
        projeto = params.get("projeto")
        status = params.get("status")

        if programa:
            qs = qs.filter(programa__nome_programa__iexact=programa)
        if projeto:
            qs = qs.filter(nome_projeto__iexact=projeto)
        if status:
            qs = qs.filter(status__iexact=status)

        return qs.order_by(F("custo_materiais").desc(nulls_last=True))

    def get_queryset(self):
        data_inicio, data_fim = self._get_date_range()
        return self._build_queryset(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=self.request.query_params,
        )


class ConsolidatedDashboardPeriodoView(ConsolidatedDashboardView):
    """
    Endpoint dedicado para filtro por período no dashboard consolidado.

    Rota: GET /api/consolidated/periodo/<YYYY-MM>/

    Herda _build_queryset e _parse_periodo de ConsolidatedDashboardView.

    Exemplos
    --------
    GET /api/consolidated/periodo/2024-03/
    GET /api/consolidated/periodo/2024-03/?programa=Cloud
    GET /api/consolidated/periodo/2024-03/?status=Em Andamento
    """

    def get_queryset(self):
        raw_periodo = self.kwargs.get("periodo", "")
        data_inicio, data_fim = self._parse_periodo(raw_periodo)
        return self._build_queryset(
            data_inicio=data_inicio,
            data_fim=data_fim,
            params=self.request.query_params,
        )
