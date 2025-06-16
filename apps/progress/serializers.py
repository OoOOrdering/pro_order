from rest_framework import serializers

from apps.order.serializers import OrderSerializer  # OrderSerializer가 필요하다고 가정
from apps.user.serializers import UserSerializer  # UserSerializer가 필요하다고 가정

from .models import Progress


class ProgressSerializer(serializers.ModelSerializer):
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
