from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.response import BaseResponseMixin

from .models import ChatRoom, ChatRoomParticipant
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomParticipantAddSerializer,
    ChatRoomParticipantRemoveSerializer,
    ChatRoomSerializer,
    ChatRoomUpdateSerializer,
)


class ChatRoomListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
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
        # 예시: 채팅방별 참여자 수 집계, 필요한 필드만 조회
        return (
            ChatRoom.objects.filter(
                room_participants__user=self.request.user,
                room_participants__left_at__isnull=True,
            )
            .select_related("created_by")
            .prefetch_related("participants", "room_participants")
            .only("id", "name", "created_by", "created_at")
            .annotate(participant_count=Count("participants"))
            .distinct()
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatRoomCreateSerializer
        return ChatRoomSerializer

    def perform_create(self, serializer):
        chat_room = serializer.save(created_by=self.request.user)
        # 생성 후 상세 정보를 반환하기 위해 ChatRoomSerializer 사용
        response_serializer = ChatRoomSerializer(chat_room, context={"request": self.request})
        self.logger.info(
            f"ChatRoom created by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )
        return self.success(data=response_serializer.data, message="채팅방이 생성되었습니다.", status=201)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_create(serializer)


class ChatRoomDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ChatRoomUpdateSerializer
        return ChatRoomSerializer

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # 수정 또는 삭제 시에는 creator인지 확인
        if request.method in ["PUT", "PATCH", "DELETE"]:
            if obj.created_by != request.user:
                self.permission_denied(request, message="채팅방 생성자만 수정/삭제할 수 있습니다.")


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

            try:
                participant = chat_room.room_participants.get(user=request.user, left_at__isnull=True)
                # 방장은 나갈 수 없음
                if participant.is_admin:
                    return Response({"error": "방장은 채팅방을 나갈 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
                participant.left_at = timezone.now()
                participant.save()
                return Response({"message": "채팅방을 나갔습니다."})
            except ChatRoomParticipant.DoesNotExist:
                return Response(
                    {"error": "채팅방 참여자가 아닙니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )
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


class ChatRoomJoinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            chat_room = ChatRoom.objects.get(pk=pk)

            # 이미 참여중인지 확인
            if chat_room.room_participants.filter(user=request.user, left_at__isnull=True).exists():
                return Response({"error": "이미 참여 중인 채팅방입니다."}, status=status.HTTP_400_BAD_REQUEST)

            # 최대 참여자 수 확인
            current_participants = chat_room.room_participants.filter(left_at__isnull=True).count()
            if current_participants >= chat_room.max_participants:
                return Response({"error": "채팅방이 가득 찼습니다."}, status=status.HTTP_400_BAD_REQUEST)

            # 참여자 추가
            ChatRoomParticipant.objects.create(chat_room=chat_room, user=request.user, is_admin=False)

            return Response({"message": "채팅방에 참여했습니다."})
        except ChatRoom.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
