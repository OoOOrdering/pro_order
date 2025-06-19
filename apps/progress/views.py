import logging

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions

from utils.response import BaseResponseMixin

from .models import Progress
from .serializers import ProgressCreateUpdateSerializer, ProgressListSerializer, ProgressSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_staff


class ProgressListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    logger = logging.getLogger("apps")
    queryset = Progress.objects.all()
    serializer_class = ProgressListSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "status": ["exact"],
        "current_step": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
        "estimated_completion_date": ["gte", "lte"],
        "actual_completion_date": ["gte", "lte"],
    }
    search_fields = ["order__order_number", "notes", "current_step"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "status",
        "estimated_completion_date",
        "actual_completion_date",
    ]
    ordering = ["-created_at"]

    @swagger_auto_schema(
        operation_summary="진행상황 목록 조회",
        operation_description="진행상황(Progress) 목록을 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 진행상황 목록을 반환합니다.", ProgressListSerializer(many=True)),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="진행상황 등록",
        operation_description="새로운 진행상황(Progress)을 등록합니다. (관리자만 가능)",
        responses={
            201: openapi.Response("진행상황이 성공적으로 등록되었습니다.", ProgressListSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Progress.objects.none()
        queryset = Progress.objects.all()

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(order__order_number__icontains=search_query)
                | Q(notes__icontains=search_query)
                | Q(current_step__icontains=search_query),
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method in ["POST"]:
            return ProgressCreateUpdateSerializer
        return ProgressListSerializer

    def perform_create(self, serializer):
        serializer.save(last_updated_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 인스턴스를 전체 필드로 직렬화
        response_serializer = ProgressListSerializer(serializer.instance)
        data = response_serializer.data
        self.logger.info(f"Progress created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="진행상황이 생성되었습니다.", status=201)


class ProgressDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    logger = logging.getLogger("apps")
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsStaffOrReadOnly]

    @swagger_auto_schema(
        operation_summary="진행상황 상세 조회",
        operation_description="특정 진행상황의 상세 정보를 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 진행상황 상세 정보를 반환합니다.", ProgressSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "진행상황을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="진행상황 수정",
        operation_description="진행상황 정보를 수정합니다. (관리자만 가능)",
        responses={
            200: openapi.Response("진행상황이 성공적으로 수정되었습니다.", ProgressSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "진행상황을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="진행상황 부분 수정",
        operation_description="진행상황 정보를 부분 수정합니다. (관리자만 가능)",
        responses={
            200: openapi.Response("진행상황이 성공적으로 수정되었습니다.", ProgressSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "진행상황을 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="진행상황 삭제",
        operation_description="진행상황을 삭제합니다. (관리자만 가능)",
        responses={
            204: "진행상황이 성공적으로 삭제되었습니다.",
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "진행상황을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Progress.objects.none()
        return super().get_queryset()

    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)
        self.logger.info(
            f"Progress updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        self.logger.info(
            f"Progress deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="진행상황 상세 정보를 조회했습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = ProgressSerializer(instance)
        return self.success(data=response_serializer.data, message="진행상황이 수정되었습니다.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="진행상황이 삭제되었습니다.", status=204)
