from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware

from core.views import BaseFilteredListView
from costs.serializers import GoldCostsSerializer
from sca_data.models import GoldCosts
from users.permissions import CanAccessCosts

from datetime import datetime, time


class GoldCostsTableView(BaseFilteredListView):
    serializer_class = GoldCostsSerializer
    permission_classes = [CanAccessCosts]
    cache_key_prefix = "gold_costs"

    def get_queryset(self):
        queryset = GoldCosts.objects.all()
        params = self.request.query_params

        filters = {
            "nome_programa": params.get("nome_programa"),
            "gerente_programa": params.get("gerente_programa"),
            "nome_projeto": params.get("nome_projeto"),
            "responsavel_projeto": params.get("responsavel_projeto"),
        }

        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})

        data_gte = params.get("data_gte")
        data_lte = params.get("data_lte")

        if data_gte and (dt := parse_date(data_gte)):
            start = make_aware(datetime.combine(dt, time.min))
            queryset = queryset.filter(data__gte=start)

        if data_lte and (dt := parse_date(data_lte)):
            end = make_aware(datetime.combine(dt, time.max))
            queryset = queryset.filter(data__lte=end)

        return queryset.order_by("data")
