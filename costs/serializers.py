from rest_framework import serializers
from sca_data.models import GoldCosts


class GoldCostsSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = GoldCosts
        fields = "__all__"

    def get_data(self, obj):
        if obj.data:
            return obj.data.date()
        return None
