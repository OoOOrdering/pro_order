from rest_framework import serializers

from apps.order.serializers import OrderSerializer
from apps.user.serializers import UserSerializer
from utils.serializers import BaseSerializer

from .models import Work


class WorkSerializer(BaseSerializer):
    order = OrderSerializer(read_only=True)
    assignee: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(read_only=True)
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


class WorkCreateUpdateSerializer(BaseSerializer):
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
