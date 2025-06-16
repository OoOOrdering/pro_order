from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import CSReply


class CSReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = CSReply
        fields = ("id", "post", "author", "content", "created_at", "updated_at")
        read_only_fields = ("author", "created_at", "updated_at")


class CSReplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSReply
        fields = ("post", "content")


class CSReplyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSReply
        fields = ("content",)
