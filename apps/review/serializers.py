from rest_framework import serializers

from apps.order.serializers import OrderSerializer  # OrderSerializer가 필요하다고 가정
from apps.user.serializers import UserSerializer  # UserSerializer가 필요하다고 가정
from utils.serializers import BaseSerializer

from .models import Review, ReviewReport


class ReviewSerializer(BaseSerializer):
    class Meta:
        model = Review
        fields = (
            "id",
            "order",
            "reviewer",
            "rating",
            "comment",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("reviewer", "created_at", "updated_at")


class ReviewCreateUpdateSerializer(BaseSerializer):
    class Meta:
        model = Review
        fields = ("id", "order", "reviewer", "rating", "comment", "is_public", "created_at", "updated_at")
        read_only_fields = ("reviewer", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
