from rest_framework import serializers
from sca_data.models import SilverTempoTarefa


class TechnicalHoursTableSerializer(serializers.ModelSerializer):
    horas_trabalhadas = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    custo_por_hora = serializers.DecimalField(
        max_digits=12, decimal_places=2, coerce_to_string=False
    )
    custo_total = serializers.DecimalField(
        max_digits=14, decimal_places=2, coerce_to_string=False
    )
    colaborador = serializers.SerializerMethodField()
    funcao = serializers.SerializerMethodField()
    projeto = serializers.SerializerMethodField()
    programa = serializers.SerializerMethodField()
    periodo = serializers.SerializerMethodField()
    tarefa = serializers.SerializerMethodField()

    class Meta:
        model = SilverTempoTarefa
        fields = [
            "id",
            "colaborador",
            "funcao",
            "projeto",
            "programa",
            "horas_trabalhadas",
            "custo_por_hora",
            "custo_total",
            "periodo",
            "tarefa",
        ]

    def _tarefa(self, obj):
        return getattr(obj, "tarefa", None)

    def get_colaborador(self, obj):
        return getattr(obj, "usuario", None)

    def get_funcao(self, obj):
        return self._tarefa(obj).responsavel if self._tarefa(obj) else None

    def get_projeto(self, obj):
        t = self._tarefa(obj)
        return t.projeto.nome_projeto if t and t.projeto else None

    def get_programa(self, obj):
        t = self._tarefa(obj)
        return (
            t.projeto.programa.nome_programa
            if t and t.projeto and t.projeto.programa
            else None
        )

    def get_periodo(self, obj):
        data = getattr(obj, "data", None)
        return data.strftime("%Y-%m") if data else None

    def get_tarefa(self, obj):
        t = self._tarefa(obj)
        return t.titulo if t else None
