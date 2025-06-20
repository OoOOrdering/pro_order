from rest_framework import serializers

from apps.order.serializers import OrderSerializer  # OrderSerializer가 필요하다고 가정
from apps.user.serializers import UserSerializer  # UserSerializer가 필요하다고 가정
from utils.profanity_filter import ProfanityFilter
from utils.serializers import BaseSerializer

from .models import Review, ReviewReport

profanity_filter = ProfanityFilter()


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

    def validate(self, attrs):
        if profanity_filter.contains_profanity(attrs.get("comment", "")):
            raise serializers.ValidationError({"comment": "리뷰 내용에 부적절한 단어가 포함되어 있습니다."})
        return attrs

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
