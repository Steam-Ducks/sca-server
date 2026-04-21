from rest_framework import generics
from rest_framework.exceptions import ValidationError
from django.db.models import ExpressionWrapper, F, FloatField
from sca_data.models import SilverTempoTarefa
from technical_hours.serializers import TechnicalHoursTableSerializer



class TechnicalHoursTableView(generics.ListAPIView):
    serializer_class = TechnicalHoursTableSerializer

    def _build_period_filters(self):
        periodo = self.request.query_params.get("periodo")
        ano = self.request.query_params.get("ano")
        mes = self.request.query_params.get("mes")

        filters = {}

        if periodo:
            try:
                ano_str, mes_str = periodo.split("-")
                filters["data__year"] = int(ano_str)
                filters["data__month"] = int(mes_str)
            except (ValueError, AttributeError):
                raise ValidationError({"periodo": "Formato inválido. Use YYYY-MM."})
        else:
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
