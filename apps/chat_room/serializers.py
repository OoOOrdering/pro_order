from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import ChatRoom, ChatRoomParticipant


class ChatRoomParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ChatRoomParticipant
        fields = ("id", "user", "is_admin", "joined_at", "left_at", "last_read_at")
        read_only_fields = ("id", "joined_at", "left_at")


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    room_participants = ChatRoomParticipantSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = (
            "id",
            "name",
            "room_type",
            "created_by",
            "participants",
            "room_participants",
            "is_active",
            "created_at",
            "updated_at",
            "last_message_at",
            "unread_count",
        )
        read_only_fields = ("id", "created_at", "updated_at", "last_message_at")

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                participant = obj.room_participants.get(user=request.user)
                if participant.last_read_at:
                    return obj.messages.filter(created_at__gt=participant.last_read_at).count()
                return obj.messages.count()
            except ChatRoomParticipant.DoesNotExist:
                return 0
        return 0


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=True)

    class Meta:
        model = ChatRoom
        fields = ("name", "room_type", "participant_ids")

    def validate(self, attrs):
        participant_ids = attrs["participant_ids"]
        if len(participant_ids) < 2:
            raise serializers.ValidationError("최소 2명 이상의 참여자가 필요합니다.")
        return attrs

    def create(self, validated_data):
        participant_ids = validated_data.pop("participant_ids")
        chat_room = ChatRoom.objects.create(created_by=self.context["request"].user, **validated_data)

        # 참여자 추가
        for user_id in participant_ids:
            ChatRoomParticipant.objects.create(
                chat_room=chat_room,
                user_id=user_id,
                is_admin=(user_id == self.context["request"].user.id),
            )

        return chat_room


class ChatRoomUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ("name", "is_active")


class ChatRoomParticipantAddSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=True)


class ChatRoomParticipantRemoveSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), required=True)
