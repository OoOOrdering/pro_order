from rest_framework import serializers

from apps.order.serializers import OrderSerializer
from apps.user.serializers import UserSerializer

from .models import Work


class WorkSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    work_type_display = serializers.CharField(source="get_work_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Work
        fields = (
            "id",
            "order",
            "assignee",
            "work_type",
            "work_type_display",
            "title",
            "description",
            "status",
            "status_display",
            "due_date",
            "completed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "completed_at")


class WorkCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = (
            "order",
            "assignee",
            "work_type",
            "title",
            "description",
            "status",
            "due_date",
            "completed_at",
        )
