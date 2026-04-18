from rest_framework import serializers

from sca_data.models import SilverProjeto


class ConsolidatedDashboardSerializer(serializers.ModelSerializer):
    programa = serializers.SerializerMethodField()
    custo_materiais = serializers.SerializerMethodField()
    custo_horas = serializers.SerializerMethodField()
    custo_total = serializers.SerializerMethodField()
    qtd_materiais = serializers.SerializerMethodField()
    total_horas = serializers.SerializerMethodField()

    class Meta:
        model = SilverProjeto
        fields = [
            "id",
            "nome_projeto",
            "programa",
            "custo_materiais",
            "custo_horas",
            "custo_total",
            "qtd_materiais",
            "total_horas",
            "status",
        ]

    def get_programa(self, obj):
        return obj.programa.nome_programa if obj.programa else None

    def get_custo_materiais(self, obj):
        return round(getattr(obj, "custo_materiais", None) or 0, 2)

    def get_custo_horas(self, obj):
        return round(getattr(obj, "custo_horas", None) or 0, 2)

    def get_custo_total(self, obj):
        materiais = getattr(obj, "custo_materiais", None) or 0
        horas = getattr(obj, "custo_horas", None) or 0
        return round(materiais + horas, 2)

    def get_qtd_materiais(self, obj):
        return getattr(obj, "qtd_materiais", None) or 0

    def get_total_horas(self, obj):
        return round(getattr(obj, "total_horas", None) or 0, 2)
