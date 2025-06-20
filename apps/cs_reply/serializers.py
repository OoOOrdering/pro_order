from rest_framework import serializers

from apps.cs_post.models import CSPost
from apps.cs_post.serializers import CSPostSerializer
from apps.user.serializers import UserSerializer
from utils.profanity_filter import ProfanityFilter

from .models import CSReply

profanity_filter = ProfanityFilter()


class CSPostMinimalSerializer(serializers.ModelSerializer):
    """CSPost의 간단한 정보만 포함하는 시리얼라이저"""

    class Meta:
        model = CSPost
        fields = ("id", "title", "post_type", "status")


class CSReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    post = CSPostMinimalSerializer(read_only=True)

    class Meta:
        model = CSReply
        fields = ("id", "post", "author", "content", "created_at", "updated_at")
        read_only_fields = ("author", "post", "created_at", "updated_at")


class CSReplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSReply
        fields = ("content",)

    def validate(self, attrs):
        if profanity_filter.contains_profanity(attrs.get("content", "")):
            raise serializers.ValidationError({"content": "답변 내용에 부적절한 단어가 포함되어 있습니다."})
        return attrs


class CSReplyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSReply
        fields = ("content",)

    def validate(self, attrs):
        if profanity_filter.contains_profanity(attrs.get("content", "")):
            raise serializers.ValidationError({"content": "답변 내용에 부적절한 단어가 포함되어 있습니다."})
        return attrs
