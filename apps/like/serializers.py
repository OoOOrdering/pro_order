from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import Like


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    content_type_name = serializers.CharField(source="content_type.model", read_only=True)
    content_object_data = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = (
            "id",
            "user",
            "content_type",
            "content_type_name",
            "object_id",
            "content_object_data",
            "created_at",
        )
        read_only_fields = ("user", "created_at")

    def get_content_object_data(self, obj):
        """연결된 객체의 기본 정보를 반환"""
        content_object = obj.content_object
        if hasattr(content_object, "to_dict"):
            return content_object.to_dict()
        return {
            "id": content_object.id,
            "str_representation": str(content_object),
            "type": obj.content_type.model,
        }


class LikeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("content_type", "object_id")

    def validate(self, data):
        user = self.context["request"].user
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if Like.objects.filter(user=user, content_type=content_type, object_id=object_id).exists():
            raise serializers.ValidationError("You have already liked this item.")
        return data

    def to_representation(self, instance):
        return LikeSerializer(instance).data
