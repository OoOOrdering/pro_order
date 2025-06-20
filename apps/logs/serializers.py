from rest_framework import serializers

from .models import ActionLog


class ActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionLog
        fields = ("id", "user", "action", "detail", "created_at")
        read_only_fields = ("id", "user", "created_at")
