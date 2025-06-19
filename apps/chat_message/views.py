from datetime import timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions

from utils.response import BaseResponseMixin

from .models import ChatMessage
from .serializers import ChatMessageCreateSerializer, ChatMessageSerializer, ChatMessageUpdateSerializer


class ChatMessageListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["message_type", "sender", "read_by"]
    search_fields = ["content", "file_url"]
    ordering_fields = ["timestamp", "message_type"]
    pagination_class = None  # 페이지네이션 비활성화

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ChatMessage.objects.none()
        chat_room_id = self.kwargs["chat_room_pk"]
        return ChatMessage.objects.filter(chat_room__id=chat_room_id).order_by("timestamp")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @swagger_auto_schema(
        operation_summary="채팅 메시지 목록 조회",
        operation_description="특정 채팅방의 메시지 목록을 조회합니다.",
        tags=["ChatMessage"],
        responses={
            200: openapi.Response("채팅 메시지 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            404: "채팅방을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return self.success(data=response.data, message="채팅 메시지 목록을 조회했습니다.")

    @swagger_auto_schema(
        operation_summary="채팅 메시지 생성",
        operation_description="특정 채팅방에 메시지를 전송합니다.",
        tags=["ChatMessage"],
        responses={
            201: openapi.Response("채팅 메시지가 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            404: "채팅방을 찾을 수 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        return self.success(data=data, message="채팅 메시지가 생성되었습니다.", status=201)


class ChatMessageDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ChatMessage.objects.none()
        chat_room_id = self.kwargs["chat_room_pk"]
        return ChatMessage.objects.select_related("sender", "chat_room").filter(chat_room__id=chat_room_id)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ChatMessageUpdateSerializer
        return ChatMessageSerializer

    def perform_update(self, serializer):
        # 메시지 작성자만 수정 가능하도록 제한 및 시간 제한 추가
        if serializer.instance.sender != self.request.user:
            self.permission_denied(self.request)

        # 5분 이내에만 수정 가능
        time_limit = timedelta(minutes=5)
        if timezone.now() - serializer.instance.timestamp > time_limit:
            self.permission_denied(self.request, message="메시지 전송 후 5분 이내에만 수정할 수 있습니다.")

        super().perform_update(serializer)
        self.logger.info(
            f"ChatMessage updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        # 메시지 작성자만 삭제 가능하도록 제한 및 시간 제한 추가
        if instance.sender != self.request.user:
            self.permission_denied(self.request)

        # 5분 이내에만 삭제 가능
        time_limit = timedelta(minutes=5)
        if timezone.now() - instance.timestamp > time_limit:
            self.permission_denied(self.request, message="메시지 전송 후 5분 이내에만 삭제할 수 있습니다.")

        super().perform_destroy(instance)
        self.logger.info(
            f"ChatMessage deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    @swagger_auto_schema(
        operation_summary="채팅 메시지 상세 조회",
        operation_description="특정 채팅 메시지의 상세 정보를 조회합니다.",
        tags=["ChatMessage"],
        responses={
            200: openapi.Response("채팅 메시지 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅 메시지를 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="채팅 메시지 정보를 조회했습니다.")

    @swagger_auto_schema(
        operation_summary="채팅 메시지 수정",
        operation_description="특정 채팅 메시지의 내용을 수정합니다. 작성자만 수정할 수 있습니다.",
        tags=["ChatMessage"],
        responses={
            200: openapi.Response("채팅 메시지가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅 메시지를 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = ChatMessageSerializer(instance)
        return self.success(data=response_serializer.data, message="채팅 메시지가 수정되었습니다.")

    @swagger_auto_schema(
        operation_summary="채팅 메시지 부분 수정",
        operation_description="특정 채팅 메시지의 일부 내용을 수정합니다. 작성자만 수정할 수 있습니다.",
        tags=["ChatMessage"],
        responses={
            200: openapi.Response("채팅 메시지가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅 메시지를 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = ChatMessageSerializer(instance)
        return self.success(data=response_serializer.data, message="채팅 메시지가 수정되었습니다.")

    @swagger_auto_schema(
        operation_summary="채팅 메시지 삭제",
        operation_description="특정 채팅 메시지를 삭제합니다. 작성자만 삭제할 수 있습니다.",
        tags=["ChatMessage"],
        responses={
            204: openapi.Response("채팅 메시지가 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "채팅 메시지를 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="채팅 메시지가 삭제되었습니다.", status=204)
