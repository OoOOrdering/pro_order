from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatRoom, ChatRoomParticipant
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomParticipantAddSerializer,
    ChatRoomParticipantRemoveSerializer,
    ChatRoomSerializer,
    ChatRoomUpdateSerializer,
)


class ChatRoomListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["room_type", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "updated_at", "last_message_at", "name"]

    def get_queryset(self):
        queryset = ChatRoom.objects.filter(
            room_participants__user=self.request.user,
            room_participants__left_at__isnull=True,
        )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ChatRoomDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(
            room_participants__user=self.request.user,
            room_participants__left_at__isnull=True,
        ).distinct()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ChatRoomUpdateSerializer
        return ChatRoomSerializer


class ChatRoomParticipantAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)
            # 관리자 권한 확인
            if not chat_room.room_participants.filter(user=request.user, is_admin=True).exists():
                return Response(
                    {"error": "관리자만 참여자를 추가할 수 있습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ChatRoomParticipantAddSerializer(data=request.data)
            if serializer.is_valid():
                user_ids = serializer.validated_data["user_ids"]
                for user_id in user_ids:
                    ChatRoomParticipant.objects.get_or_create(
                        chat_room=chat_room,
                        user_id=user_id,
                        defaults={"is_admin": False},
                    )
                return Response({"message": "참여자가 추가되었습니다."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChatRoomParticipantRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)
            # 관리자 권한 확인
            if not chat_room.room_participants.filter(user=request.user, is_admin=True).exists():
                return Response(
                    {"error": "관리자만 참여자를 제거할 수 있습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ChatRoomParticipantRemoveSerializer(data=request.data)
            if serializer.is_valid():
                user_ids = serializer.validated_data["user_ids"]
                ChatRoomParticipant.objects.filter(chat_room=chat_room, user_id__in=user_ids).update(
                    left_at=timezone.now(),
                )
                return Response({"message": "참여자가 제거되었습니다."})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChatRoomLeaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)
            participant = chat_room.room_participants.get(user=request.user, left_at__isnull=True)
            participant.left_at = timezone.now()
            participant.save()
            return Response({"message": "채팅방을 나갔습니다."})
        except (ChatRoom.DoesNotExist, ChatRoomParticipant.DoesNotExist):
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ChatRoomMarkAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)
            participant = chat_room.room_participants.get(user=request.user, left_at__isnull=True)
            participant.last_read_at = timezone.now()
            participant.save()
            return Response({"message": "모든 메시지를 읽음 처리했습니다."})
        except (ChatRoom.DoesNotExist, ChatRoomParticipant.DoesNotExist):
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
