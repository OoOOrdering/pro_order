from rest_framework import generics, permissions
from rest_framework.response import Response

from utils.response import BaseResponseMixin

from .models import DashboardSummary
from .serializers import DashboardSummarySerializer


class DashboardSummaryListView(BaseResponseMixin, generics.ListAPIView):
    queryset = DashboardSummary.objects.all().order_by("-last_updated")
    serializer_class = DashboardSummarySerializer
    permission_classes = [permissions.IsAdminUser]  # 관리자만 접근 가능
    filterset_fields = ["user"]  # 사용자별 필터링

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
    permission_classes = [permissions.IsAdminUser]  # 관리자만 접근 가능

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
