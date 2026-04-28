from rest_framework import serializers
from sca_data.models import GoldCosts


class GoldCostsSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = GoldCosts
        fields = "__all__"

    def get_data(self, obj):
        if not obj.data:
            return None

        if hasattr(obj.data, "date"):
            return obj.data.date().isoformat()

        return obj.data.isoformat() if hasattr(obj.data, "isoformat") else obj.data
