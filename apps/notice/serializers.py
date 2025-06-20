from rest_framework import serializers

from apps.user.serializers import UserSerializer
from utils.profanity_filter import ProfanityFilter

from .models import Notice

profanity_filter = ProfanityFilter()


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

    def validate(self, attrs):
        if profanity_filter.contains_profanity(attrs.get("title", "")):
            raise serializers.ValidationError({"title": "제목에 부적절한 단어가 포함되어 있습니다."})
        if profanity_filter.contains_profanity(attrs.get("content", "")):
            raise serializers.ValidationError({"content": "내용에 부적절한 단어가 포함되어 있습니다."})
        return attrs
