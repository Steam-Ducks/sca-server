from rest_framework import serializers
from sca_data.models import GoldCosts


class GoldCostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldCosts
        fields = "__all__"
