from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
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
        if getattr(self, "swagger_fake_view", False):
            return ChatRoom.objects.none()
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

    @swagger_auto_schema(
        operation_summary="채팅방 목록 조회",
        operation_description="본인이 참여 중인 채팅방 목록을 조회합니다. 검색, 정렬, 필터링이 가능합니다.",
        tags=["ChatRoom"],
        responses={
            200: openapi.Response("채팅방 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        """채팅방 목록 조회"""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="채팅방 생성",
        operation_description="새로운 채팅방을 생성합니다. 생성 시 본인이 방장으로 등록됩니다.",
        tags=["ChatRoom"],
        responses={
            201: openapi.Response("채팅방이 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        """채팅방 생성"""
        return super().post(request, *args, **kwargs)

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
        if getattr(self, "swagger_fake_view", False):
            return ChatRoom.objects.none()
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

    @swagger_auto_schema(
        operation_summary="채팅방 상세 조회",
        operation_description="특정 채팅방의 상세 정보를 조회합니다.",
        tags=["ChatRoom"],
        responses={
            200: openapi.Response("채팅방 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅방을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        """채팅방 상세 조회"""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="채팅방 수정",
        operation_description="채팅방의 정보를 수정합니다. 방장만 수정할 수 있습니다.",
        tags=["ChatRoom"],
        responses={
            200: openapi.Response("채팅방 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅방을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        """채팅방 수정"""
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="채팅방 삭제",
        operation_description="채팅방을 삭제합니다. 방장만 삭제할 수 있습니다.",
        tags=["ChatRoom"],
        responses={
            204: openapi.Response("채팅방이 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅방을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        """채팅방 삭제"""
        return super().delete(request, *args, **kwargs)


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
