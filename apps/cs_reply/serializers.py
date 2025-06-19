from rest_framework import serializers

from apps.cs_post.models import CSPost
from apps.cs_post.serializers import CSPostSerializer
from apps.user.serializers import UserSerializer

from .models import CSReply


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
        fields = ("content",)  # post는 URL에서 가져오므로 제외


class CSReplyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSReply
        fields = ("content",)
