from rest_framework import serializers
from sca_data.models import AuditExecutionLog


class AuditExecutionLogSerializer(serializers.ModelSerializer):
    run_id = serializers.SerializerMethodField()
    operation_metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditExecutionLog
        fields = "__all__"

    def get_run_id(self, obj):
        return str(obj.run_id) if obj.run_id else None

    def get_operation_metadata(self, obj):
        return obj.operation_metadata if obj.operation_metadata else None

