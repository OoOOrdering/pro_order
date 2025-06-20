from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.response import Response

from apps.user.permissions_role import IsAdmin
from utils.response import BaseResponseMixin

from .models import DashboardSummary
from .serializers import DashboardSummarySerializer


class DashboardSummaryListView(BaseResponseMixin, generics.ListAPIView):
    queryset = DashboardSummary.objects.all().order_by("-last_updated")
    serializer_class = DashboardSummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]  # 인증 + 관리자만 접근 가능
    filterset_fields = ["user"]  # 사용자별 필터링

    @swagger_auto_schema(
        operation_summary="대시보드 요약 정보 목록 조회",
        operation_description="관리자 권한으로 전체 대시보드 요약 정보 목록을 조회합니다. 사용자별 필터링이 가능합니다.",
        tags=["Dashboard"],
        responses={
            200: openapi.Response("대시보드 요약 정보 목록 조회 성공", DashboardSummarySerializer(many=True)),
            401: "인증 필요",
            403: "관리자 권한 필요",
        },
    )
    def get(self, request, *args, **kwargs):
        """대시보드 요약 정보 목록 조회"""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DashboardSummary.objects.none()
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            self.logger.info(
                f"DashboardSummary list viewed by {request.user.email if request.user.is_authenticated else 'anonymous'}"
            )
            return self.success(data=paginated_response.data, message="대시보드 요약 정보 목록을 조회했습니다.")

        serializer = self.get_serializer(queryset, many=True)
        self.logger.info(
            f"DashboardSummary list viewed by {request.user.email if request.user.is_authenticated else 'anonymous'}"
        )
        return self.success(
            data={"count": len(serializer.data), "next": None, "previous": None, "results": serializer.data},
            message="대시보드 요약 정보 목록을 조회했습니다.",
        )


class DashboardSummaryView(BaseResponseMixin, generics.RetrieveAPIView):
    serializer_class = DashboardSummarySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]  # 인증 + 관리자만 접근 가능

    @swagger_auto_schema(
        operation_summary="대시보드 요약 정보 상세 조회",
        operation_description="특정 대시보드 요약 정보의 상세 내용을 조회합니다. 관리자만 전체, 일반 사용자는 본인 정보만 조회할 수 있습니다.",
        tags=["Dashboard"],
        responses={
            200: openapi.Response("대시보드 요약 정보 상세 조회 성공", DashboardSummarySerializer),
            401: "인증 필요",
            403: "관리자 권한 필요",
            404: "대시보드 정보를 찾을 수 없음",
        },
    )
    def get(self, request, *args, **kwargs):
        """대시보드 요약 정보 상세 조회"""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DashboardSummary.objects.none()
        return super().get_queryset()

    def get_object(self):
        # 전역 대시보드 요약의 경우 user가 None인 객체를 반환
        if self.kwargs.get("pk") is None:
            return DashboardSummary.objects.filter(user__isnull=True).first()
        return DashboardSummary.objects.get(pk=self.kwargs["pk"])

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        if instance.user is None:
            message = "전역 대시보드 요약 정보를 조회했습니다."
        else:
            message = "대시보드 요약 정보를 조회했습니다."
        self.logger.info(
            f"DashboardSummary detail viewed by {request.user.email if request.user.is_authenticated else 'anonymous'}"
        )
        return self.success(data=serializer.data, message=message)
