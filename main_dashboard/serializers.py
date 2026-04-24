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