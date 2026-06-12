from rest_framework import serializers

from sca_data.models import FatoExecucaoCarga


class FatoExecucaoCargaSerializer(serializers.ModelSerializer):
    duracao_segundos = serializers.SerializerMethodField()

    class Meta:
        model = FatoExecucaoCarga
        fields = [
            "id",
            "run_id",
            "fonte",
            "tabela",
            "tipo_processo",
            "status",
            "linhas_processadas",
            "erros",
            "avisos",
            "duracao_segundos",
            "detalhes_falha",
            "iniciado_em",
            "finalizado_em",
        ]

    def get_duracao_segundos(self, obj):
        if obj.finalizado_em and obj.iniciado_em:
            return int((obj.finalizado_em - obj.iniciado_em).total_seconds())
        return None
