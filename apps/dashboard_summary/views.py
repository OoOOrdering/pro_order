from rest_framework import generics, permissions

from .models import DashboardSummary
from .serializers import DashboardSummarySerializer


class DashboardSummaryListView(generics.ListAPIView):
    queryset = DashboardSummary.objects.all()
    serializer_class = DashboardSummarySerializer
    filterset_fields = ["summary_date"]  # 날짜 필터링 추가


class DashboardSummaryDetailView(generics.RetrieveAPIView):
    queryset = DashboardSummary.objects.all()
    serializer_class = DashboardSummarySerializer
    lookup_field = "summary_date"  # 날짜로 조회


class DashboardSummaryView(generics.RetrieveAPIView):
    serializer_class = DashboardSummarySerializer
    permission_classes = [permissions.IsAdminUser]  # 관리자만 접근 가능

    def get_object(self):
        # 전역 대시보드 요약 (user=None) 또는 현재 사용자의 대시보드 요약을 가져옵니다.
        # 여기서는 일단 전역 대시보드 요약만 가정합니다.
        obj, created = DashboardSummary.objects.get_or_create(user__isnull=True)
        return obj
