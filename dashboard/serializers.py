# dashboard/serializers.py
from rest_framework import serializers


class DashboardKPIsSerializer(serializers.Serializer):
    total_consolidated_cost = serializers.FloatField()
    total_materials_cost = serializers.FloatField()
    total_hours_cost = serializers.FloatField()
    total_projects = serializers.IntegerField()
    total_programs = serializers.IntegerField()
    