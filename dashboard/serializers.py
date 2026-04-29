# dashboard/serializers.py
from rest_framework import serializers

from sca_data.models import SilverProjeto


class DashboardKPIsSerializer(serializers.Serializer):
    total_consolidated_cost = serializers.FloatField()
    total_materials_cost = serializers.FloatField()
    total_hours_cost = serializers.FloatField()
    total_projects = serializers.IntegerField()
    total_programs = serializers.IntegerField()


class MainDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SilverProjeto
        fields = ["id", "nome_projeto", "status"]


class ProgramSummarySerializer(serializers.Serializer):
    programa = serializers.CharField()
    qtd_projetos = serializers.IntegerField()
    custo_materiais = serializers.FloatField()
    custo_horas = serializers.FloatField()
    custo_total = serializers.FloatField()


class CostCompositionSerializer(serializers.Serializer):
    custo_materiais = serializers.FloatField()
    custo_horas = serializers.FloatField()
    custo_total = serializers.FloatField()
    pct_materiais = serializers.FloatField()
    pct_horas = serializers.FloatField()
