from rest_framework import serializers

from sca_data.models import SilverProjeto


class BudgetProjectSerializer(serializers.ModelSerializer):
    projeto = serializers.CharField(source="nome_projeto")
    programa = serializers.SerializerMethodField()
    budget = serializers.SerializerMethodField()
    custoMateriais = serializers.SerializerMethodField()
    custoHoras = serializers.SerializerMethodField()
    custoReal = serializers.SerializerMethodField()
    desvioPercent = serializers.SerializerMethodField()
    saude = serializers.SerializerMethodField()
    projecaoEstouro = serializers.SerializerMethodField()
    periodo = serializers.SerializerMethodField()

    class Meta:
        model = SilverProjeto
        fields = [
            "id",
            "projeto",
            "programa",
            "budget",
            "custoMateriais",
            "custoHoras",
            "custoReal",
            "desvioPercent",
            "saude",
            "projecaoEstouro",
            "periodo",
            "status",
        ]

    def get_programa(self, obj):
        return obj.programa.nome_programa if obj.programa else "Sem programa"

    def get_budget(self, obj):
        return round(getattr(obj, "budget", 0) or 0, 2)

    def get_custoMateriais(self, obj):
        return round(getattr(obj, "custo_materiais", 0) or 0, 2)

    def get_custoHoras(self, obj):
        return round(getattr(obj, "custo_horas", 0) or 0, 2)

    def get_custoReal(self, obj):
        custo_materiais = getattr(obj, "custo_materiais", 0) or 0
        custo_horas = getattr(obj, "custo_horas", 0) or 0
        return round(custo_materiais + custo_horas, 2)

    def get_desvioPercent(self, obj):
        return round(getattr(obj, "desvio_percent", 0) or 0, 1)

    def get_saude(self, obj):
        return getattr(obj, "saude_financeira", "Saudável")

    def get_projecaoEstouro(self, obj):
        projection = getattr(obj, "projecao_estouro", None)
        return round(projection, 2) if projection is not None else None

    def get_periodo(self, obj):
        if obj.data_inicio:
            return obj.data_inicio.strftime("%Y-%m")
        return "Sem periodo"

