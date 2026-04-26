from rest_framework import serializers
from sca_data.models import GoldCosts
from datetime import datetime, time


class GoldCostsSerializer(serializers.ModelSerializer):
    data = serializers.DateField()

    class Meta:
        model = GoldCosts
        fields = "__all__"

    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        if "data" in value:
            value["data"] = datetime.combine(value["data"], time.min)

        return value
