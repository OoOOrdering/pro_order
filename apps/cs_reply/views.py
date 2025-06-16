from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, serializers

from apps.cs_post.models import CSPost

from .models import CSReply
from .serializers import (
    CSReplyCreateSerializer,
    CSReplySerializer,
    CSReplyUpdateSerializer,
)


class CSReplyListCreateView(generics.ListCreateAPIView):
    serializer_class = CSReplySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["author", "created_at"]
    search_fields = ["content"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        # 관리자는 모든 답변 조회, 사용자는 본인 문의글에 대한 답변만 조회
        post_pk = self.kwargs.get("cs_post_pk")
        if not post_pk:
            return CSReply.objects.none()

        queryset = CSReply.objects.filter(post__pk=post_pk)

        if not self.request.user.is_staff:
            # 일반 사용자는 자신이 작성한 CS Post의 답변만 볼 수 있습니다.
            queryset = queryset.filter(post__author=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CSReplyCreateSerializer
        return CSReplySerializer

    def perform_create(self, serializer):
        # 관리자만 답변을 작성할 수 있도록 권한 검사
        if not self.request.user.is_staff:
            self.permission_denied(self.request)

        post_pk = self.kwargs.get("cs_post_pk")
        if not post_pk:
            raise serializers.ValidationError("CS Post ID is required.")
        try:
            cs_post = CSPost.objects.get(pk=post_pk)
        except CSPost.DoesNotExist:
            raise serializers.ValidationError("CS Post not found.")

        serializer.save(author=self.request.user, post=cs_post)


class CSReplyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CSReplySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # 관리자는 모든 답변 조회, 사용자는 본인 문의글에 대한 답변만 조회/수정/삭제
        post_pk = self.kwargs.get("cs_post_pk")
        if not post_pk:
            return CSReply.objects.none()

        queryset = CSReply.objects.filter(post__pk=post_pk)

        if not self.request.user.is_staff:
            # 일반 사용자는 자신이 작성한 CS Post의 답변만 볼 수 있습니다.
            queryset = queryset.filter(post__author=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CSReplyUpdateSerializer
        return CSReplySerializer

    def perform_update(self, serializer):
        # 관리자만 수정 가능
        if not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # 관리자만 삭제 가능
        if not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
