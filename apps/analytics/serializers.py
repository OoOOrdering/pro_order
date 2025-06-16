from rest_framework import serializers

from apps.user.serializers import UserSerializer  # 사용자 시리얼라이저 임포트

from .models import DailyAnalytics, EventLog


class DailyAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAnalytics
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class EventLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # 사용자 정보를 읽기 전용으로 표시

    class Meta:
        model = EventLog
        fields = (
            "id",
            "user",
            "event_name",
            "event_type",
            "value",
            "timestamp",
            "object_id",
            "object_type",
            "metadata",
        )
        read_only_fields = ("timestamp",)
