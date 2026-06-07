from django.core.cache import cache
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from rest_framework import generics
from rest_framework.response import Response

from costs.serializers import GoldCostsSerializer
from sca_data.models import GoldCosts
from users.permissions import CanAccessCosts

from datetime import datetime, time

_CACHE_TTL = 300


def _ck(prefix, params=None):
    suffix = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()) if v)
    return f"{prefix}:{suffix}" if suffix else prefix


class GoldCostsTableView(generics.ListAPIView):
    serializer_class = GoldCostsSerializer
    permission_classes = [CanAccessCosts]

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

    def list(self, request, *args, **kwargs):
        key = _ck("gold_costs", request.query_params)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, _CACHE_TTL)
        return response
