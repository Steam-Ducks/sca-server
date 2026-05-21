from rest_framework import serializers

from sca_data.models import FatoExecucaoCarga


class FatoExecucaoCargaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FatoExecucaoCarga
        fields = [
            "id",
            "run_id",
            "fonte",
            "tabela",
            "status",
            "linhas_processadas",
            "erros",
            "avisos",
            "detalhes_falha",
            "iniciado_em",
            "finalizado_em",
        ]
