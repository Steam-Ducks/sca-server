from rest_framework import generics
from django.utils.dateparse import parse_date

from costs.serializers import GoldCostsSerializer
from sca_data.models import GoldCosts


class GoldCostsTableView(generics.ListAPIView):
    serializer_class = GoldCostsSerializer

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
            queryset = queryset.filter(data__gte=dt)

        if data_lte and (dt := parse_date(data_lte)):
            queryset = queryset.filter(data__lte=dt)

        return queryset.order_by("data")
