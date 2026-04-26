from rest_framework import serializers

from sca_data.models import SilverProjeto


class MainDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SilverProjeto
        fields = [
            "id",
            "nome_projeto",
            "status",
        ]


class ProgramSummarySerializer(serializers.Serializer):
    programa = serializers.CharField()
    qtd_projetos = serializers.IntegerField()
    custo_materiais = serializers.FloatField()
    custo_horas = serializers.FloatField()
    custo_total = serializers.FloatField()
