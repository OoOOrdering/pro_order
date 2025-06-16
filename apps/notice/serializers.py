from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Notice
        fields = (
            "id",
            "title",
            "content",
            "author",
            "is_published",
            "is_important",
            "view_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("author", "view_count", "created_at", "updated_at")


class NoticeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ("title", "content", "is_published", "is_important")
