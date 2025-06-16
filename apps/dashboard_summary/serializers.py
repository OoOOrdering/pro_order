from rest_framework import serializers

from .models import DashboardSummary


class DashboardSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSummary
        fields = "__all__"
