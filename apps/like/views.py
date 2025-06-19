from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter

from utils.response import BaseResponseMixin

from .models import Like
from .serializers import LikeCreateSerializer, LikeSerializer


class LikeFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name="created_at", lookup_expr="date__gte")
    created_at__lte = filters.DateTimeFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Like
        fields = {
            "content_type": ["exact"],
            "object_id": ["exact"],
        }


class LikeListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = LikeFilter
    ordering_fields = ["created_at"]

    @swagger_auto_schema(
        operation_summary="좋아요 목록 조회",
        operation_description="내가 누른 좋아요 목록을 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 좋아요 목록을 반환합니다.", LikeSerializer(many=True)),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="좋아요 등록",
        operation_description="새로운 좋아요를 등록합니다.",
        responses={
            201: openapi.Response("좋아요가 성공적으로 등록되었습니다.", LikeSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Like.objects.none()
        return Like.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LikeCreateSerializer
        return LikeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        self.logger.info(f"Like created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="좋아요가 생성되었습니다.", status=201)


class LikeDestroyView(BaseResponseMixin, generics.DestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    @swagger_auto_schema(
        operation_summary="좋아요 삭제",
        operation_description="좋아요를 취소(삭제)합니다.",
        responses={
            204: "좋아요가 성공적으로 삭제되었습니다.",
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "좋아요를 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Like.objects.none()
        return super().get_queryset()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.logger.info(f"Like deleted by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=None, message="좋아요가 삭제되었습니다.", status=204)
