import datetime

from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError as DRFValidationError

from sca_data.models import SilverPedidoCompra
from materials.serializers import MaterialsTableSerializer


class MaterialsTableView(generics.ListAPIView):
    """
    Retorna os dados de compras consolidadas com filtros opcionais por período.

    Query params
    ------------
    data_inicio : str  (YYYY-MM-DD)  — bound inferior inclusivo em data_pedido
    data_fim    : str  (YYYY-MM-DD)  — bound superior inclusivo em data_pedido
    periodo     : str  (YYYY-MM)     — atalho; expande para o mês completo
                                       (ignorado quando data_inicio ou data_fim
                                       estiverem presentes)

    Prioridade: data_inicio / data_fim > periodo
    """

    serializer_class = MaterialsTableSerializer

    def _parse_date(self, raw: str, param_name: str) -> datetime.date:
        try:
            return datetime.date.fromisoformat(raw)
        except ValueError:
            raise DRFValidationError(
                {param_name: f"Data inválida '{raw}'. Use o formato YYYY-MM-DD."}
            )

    def _parse_periodo(self, raw: str) -> tuple:
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
            data_inicio = self._parse_date(raw_inicio, "data_inicio") if raw_inicio else None
            data_fim = self._parse_date(raw_fim, "data_fim") if raw_fim else None

            if data_inicio and data_fim and data_inicio > data_fim:
                raise DRFValidationError(
                    {"data_inicio": "data_inicio não pode ser posterior a data_fim."}
                )

            return data_inicio, data_fim

        if raw_periodo:
            return self._parse_periodo(raw_periodo)

        return None, None
    

    def get_queryset(self):
        data_inicio, data_fim = self._get_date_range()

        qs = (
            SilverPedidoCompra.objects.select_related(
                "solicitacao__material",
                "solicitacao__projeto__programa",
                "fornecedor",
            )
            .filter(solicitacao__isnull=False)
        )

        if data_inicio:
            qs = qs.filter(data_pedido__gte=data_inicio)   
        if data_fim:
            qs = qs.filter(data_pedido__lte=data_fim)       

        return qs.order_by("-valor_total")
