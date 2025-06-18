from rest_framework import serializers

from apps.user.serializers import UserSerializer  # 사용자 시리얼라이저가 필요하다고 가정

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    read_by = UserSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "chat_room",
            "sender",
            "message_type",
            "content",
            "file",
            "image",
            "timestamp",
            "is_read",
            "read_by",
        )
        read_only_fields = ("sender", "timestamp", "is_read", "read_by")


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("chat_room", "message_type", "content", "file", "image")

    def validate(self, data):
        if data["message_type"] == "text" and not data.get("content"):
            raise serializers.ValidationError("Text messages must have content.")
        if data["message_type"] in ["image", "file"] and not (data.get("image") or data.get("file")):
            raise serializers.ValidationError(f"{data['message_type']} messages must have a file or image.")
        return data


class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("content",)
