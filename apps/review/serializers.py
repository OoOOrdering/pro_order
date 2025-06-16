from rest_framework import serializers

from apps.order.serializers import OrderSerializer  # OrderSerializer가 필요하다고 가정
from apps.user.serializers import UserSerializer  # UserSerializer가 필요하다고 가정

from .models import Review, ReviewReport


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

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


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        model = ReviewReport
        fields = "__all__"
