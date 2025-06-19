from rest_framework import serializers

from .models import PresetMessage


class PresetMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresetMessage
        fields = [
            "id",
            "user",
            "title",
            "content",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        # user 필드를 요청한 사용자로 설정
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class PresetMessageCreateUpdateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = PresetMessage
        fields = ("title", "content", "is_active", "user")
        read_only_fields = ("user",)
