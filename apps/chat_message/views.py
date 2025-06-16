from datetime import timedelta

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import ChatMessage
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatMessageUpdateSerializer,
)


class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["message_type", "sender", "read_by__user"]
    search_fields = ["content", "file_url"]
    ordering_fields = ["timestamp", "message_type"]

    def get_queryset(self):
        chat_room_id = self.kwargs["chat_room_pk"]
        return ChatMessage.objects.filter(chat_room__id=chat_room_id).order_by("timestamp")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatMessageCreateSerializer
        return ChatMessageSerializer

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class ChatMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        chat_room_id = self.kwargs["chat_room_pk"]
        return ChatMessage.objects.filter(chat_room__id=chat_room_id)

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

    def perform_destroy(self, instance):
        # 메시지 작성자만 삭제 가능하도록 제한 및 시간 제한 추가
        if instance.sender != self.request.user:
            self.permission_denied(self.request)

        # 5분 이내에만 삭제 가능
        time_limit = timedelta(minutes=5)
        if timezone.now() - instance.timestamp > time_limit:
            self.permission_denied(self.request, message="메시지 전송 후 5분 이내에만 삭제할 수 있습니다.")

        super().perform_destroy(instance)
