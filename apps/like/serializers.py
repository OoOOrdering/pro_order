from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import Like


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    content_type_name = serializers.CharField(source="content_type.model", read_only=True)
    object_representation = serializers.SerializerMethodField()

    class Meta:
        model = Like
        fields = (
            "id",
            "user",
            "content_type",
            "content_type_name",
            "object_id",
            "content_object",
            "object_representation",
            "created_at",
        )
        read_only_fields = ("user", "created_at", "content_object")

    def get_object_representation(self, obj):
        return str(obj.content_object)


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
