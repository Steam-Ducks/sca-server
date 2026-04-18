import datetime

from consolidated.consolidated_dashboard.serializers import (
    ConsolidatedDashboardSerializer,
)
from django.db.models import ExpressionWrapper, F, FloatField, Q, Sum
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError

from sca_data.models import SilverProjeto


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
    """

    serializer_class = ConsolidatedDashboardSerializer

    # ------------------------------------------------------------------
    # Helpers de parsing
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Queryset
    #
    # SQL gerado pelo ORM:
    #
    #   SELECT
    #     projetos.id,
    #     projetos.nome_projeto,
    #     projetos.status,
    #     programas.nome_programa,
    #     SUM(pedidos_compra.valor_total)          AS custo_materiais,
    #     SUM(tempo_tarefas.horas_trabalhadas
    #         * projetos.custo_hora)               AS custo_horas,
    #     SUM(pedidos_compra.valor_total)
    #     + SUM(horas * custo_hora)                AS custo_total,
    #     SUM(solicitacoes_compra.quantidade)      AS qtd_materiais,
    #     SUM(tempo_tarefas.horas_trabalhadas)     AS total_horas
    #   FROM silver.projetos
    #   LEFT JOIN silver.programas         ON ...
    #   LEFT JOIN silver.solicitacoes_compra ON projeto_id = projetos.id
    #   LEFT JOIN silver.pedidos_compra    ON solicitacao_id = solicitacoes.id
    #     [AND data_pedido BETWEEN data_inicio AND data_fim]
    #   LEFT JOIN silver.tarefas_projeto   ON projeto_id = projetos.id
    #   LEFT JOIN silver.tempo_tarefas     ON tarefa_id = tarefas.id
    #     [AND data BETWEEN data_inicio AND data_fim]
    #   WHERE [programa / projeto / status filters]
    #   GROUP BY projetos.id, projetos.nome_projeto, projetos.status,
    #            programas.nome_programa
    #   ORDER BY custo_total DESC
    # ------------------------------------------------------------------

    def get_queryset(self):
        data_inicio, data_fim = self._get_date_range()
        params = self.request.query_params

        # Build date filters for related models
        pedido_filter = Q(solicitacoes__pedidocompra__solicitacao__isnull=False)
        tempo_filter = Q()

        if data_inicio:
            pedido_filter &= Q(solicitacoes__pedidocompra__data_pedido__gte=data_inicio)
            tempo_filter &= Q(tarefas__tempos__data__gte=data_inicio)
        if data_fim:
            pedido_filter &= Q(solicitacoes__pedidocompra__data_pedido__lte=data_fim)
            tempo_filter &= Q(tarefas__tempos__data__lte=data_fim)

        qs = SilverProjeto.objects.select_related("programa").annotate(
            # Custo materiais: soma do valor_total dos pedidos de compra do projeto
            custo_materiais=Sum(
                "solicitacoes__pedidocompra__valor_total",
                filter=pedido_filter,
            ),
            # Custo horas: soma de horas_trabalhadas * custo_hora do projeto
            custo_horas=Sum(
                ExpressionWrapper(
                    F("tarefas__tempos__horas_trabalhadas") * F("custo_hora"),
                    output_field=FloatField(),
                ),
                filter=tempo_filter,
            ),
            # Qtd materiais: soma das quantidades solicitadas
            qtd_materiais=Sum(
                "solicitacoes__quantidade",
                filter=Q(solicitacoes__pedidocompra__isnull=False),
            ),
            # Total horas trabalhadas
            total_horas=Sum(
                "tarefas__tempos__horas_trabalhadas",
                filter=tempo_filter,
            ),
        )

        # Filtros adicionais por programa, projeto e status
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
