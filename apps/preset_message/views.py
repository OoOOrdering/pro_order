import logging

from django.db import models
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from utils.response import BaseResponseMixin

from .filters import PresetMessageFilter
from .models import PresetMessage
from .serializers import PresetMessageCreateUpdateSerializer, PresetMessageSerializer


class PresetMessageListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    logger = logging.getLogger("apps")
    serializer_class = PresetMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PresetMessageFilter
    search_fields = ["title", "content", "user__username"]
    ordering_fields = ["title", "created_at", "updated_at"]
    ordering = ["title"]

    def get_queryset(self):
        queryset = PresetMessage.objects.filter(models.Q(user=self.request.user) | models.Q(user__isnull=True))

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(user__username__icontains=search_query),
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PresetMessageCreateUpdateSerializer
        return PresetMessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 인스턴스를 전체 필드로 직렬화
        response_serializer = PresetMessageSerializer(serializer.instance)
        data = response_serializer.data
        self.logger.info(
            f"PresetMessage created by {request.user.email if request.user.is_authenticated else 'anonymous'}"
        )
        return self.success(data=data, message="프리셋 메시지가 생성되었습니다.", status=201)


class PresetMessageDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    logger = logging.getLogger("apps")
    serializer_class = PresetMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return PresetMessage.objects.filter(models.Q(user=self.request.user) | models.Q(user__isnull=True))

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PresetMessageCreateUpdateSerializer
        return PresetMessageSerializer

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user and serializer.instance.user is not None:
            self.permission_denied(self.request)
        super().perform_update(serializer)
        self.logger.info(
            f"PresetMessage updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        if instance.user != self.request.user and instance.user is not None:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
        self.logger.info(
            f"PresetMessage deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="프리셋 메시지 상세 정보를 조회했습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = PresetMessageSerializer(instance)
        return self.success(data=response_serializer.data, message="프리셋 메시지가 수정되었습니다.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="프리셋 메시지가 삭제되었습니다.", status=204)
