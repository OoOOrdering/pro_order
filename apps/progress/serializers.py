from rest_framework import serializers

from apps.order.serializers import OrderSerializer
from apps.user.serializers import UserSerializer

from .models import Progress


class ProgressSerializer(serializers.ModelSerializer):
    last_updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Progress
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "last_updated_by")


class ProgressListSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    last_updated_by = UserSerializer(read_only=True)

    class Meta:
        model = Progress
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "last_updated_by")


class ProgressCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = (
            "order",
            "status",
            "current_step",
            "notes",
            "estimated_completion_date",
            "actual_completion_date",
        )
