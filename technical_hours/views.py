from rest_framework import generics
from django.db.models import ExpressionWrapper, F, FloatField
from sca_data.models import SilverTempoTarefa
from technical_hours.serializers import TechnicalHoursTableSerializer


class TechnicalHoursTableView(generics.ListAPIView):
    serializer_class = TechnicalHoursTableSerializer

    def get_queryset(self):
        return (
            SilverTempoTarefa.objects.select_related("tarefa__projeto__programa")
            .filter(tarefa__isnull=False)
            .annotate(
                custo_por_hora=F("tarefa__projeto__custo_hora"),
                custo_total=ExpressionWrapper(
                    F("horas_trabalhadas") * F("tarefa__projeto__custo_hora"),
                    output_field=FloatField(),
                ),
            )
            .order_by("-custo_total")
        )
