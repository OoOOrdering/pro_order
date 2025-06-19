from django.db.models import Avg, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from utils.response import BaseResponseMixin

from .models import DailyAnalytics, EventLog
from .serializers import DailyAnalyticsSerializer, EventLogSerializer


class DailyAnalyticsListView(generics.ListAPIView):
    queryset = DailyAnalytics.objects.all()
    serializer_class = DailyAnalyticsSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["date"]
    ordering_fields = ["date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        return queryset


class EventLogListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    serializer_class = EventLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["event_type", "user", "object_type", "object_id"]
    search_fields = ["event_name", "metadata"]
    ordering_fields = ["timestamp", "event_type", "user"]

    def get_queryset(self):
        # 예시: 이벤트 타입별 개수 집계, 필요한 필드만 조회
        qs = EventLog.objects.select_related("user").only("id", "user", "event_type", "timestamp")
        if self.request.user.is_staff:
            queryset = qs
        else:
            queryset = qs.filter(user=self.request.user)

        start_timestamp = self.request.query_params.get("start_timestamp")
        end_timestamp = self.request.query_params.get("end_timestamp")

        if start_timestamp:
            queryset = queryset.filter(timestamp__gte=start_timestamp)
        if end_timestamp:
            queryset = queryset.filter(timestamp__lte=end_timestamp)

        # queryset = queryset.annotate(event_count=Count('event_type'))  # 집계 예시
        return queryset

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        self.logger.info(f"EventLog created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="이벤트 로그가 생성되었습니다.", status=201)


class EventLogDetailView(generics.RetrieveAPIView):
    queryset = EventLog.objects.all()
    serializer_class = EventLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return EventLog.objects.all()
        return EventLog.objects.filter(user=self.request.user)


class AnalyticsListView(generics.ListAPIView):
    queryset = DailyAnalytics.objects.all()
    serializer_class = DailyAnalyticsSerializer
    filterset_fields = ["month"]  # 월별 필터링 추가


class AnalyticsDetailView(generics.RetrieveAPIView):
    queryset = DailyAnalytics.objects.all()
    serializer_class = DailyAnalyticsSerializer
    lookup_field = "month"  # 월로 조회


class AnalyticsSummaryView(BaseResponseMixin, generics.ListAPIView):
    serializer_class = DailyAnalyticsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # annotate/only/values 집계/필드최적화 예시
        qs = super().get_queryset()
        qs = qs.annotate(
            total_orders=Count("order"),
            avg_rating=Avg("review__rating"),
        ).only("user", "created_at")
        return qs


# 운영 자동화/모니터링 예시:
# - Sentry 연동: settings.py에 SENTRY_DSN 설정, sentry_sdk.init 호출
# - drf-yasg: /swagger/ 경로로 API 문서 자동화
# - Django Debug Toolbar: INSTALLED_APPS, MIDDLEWARE에 추가, 쿼리/템플릿/캐시 실시간 모니터링
# - 배포 자동화: scripts/deploy.sh 등으로 git pull, migrate, collectstatic, reload 자동화
# - DB 백업: scripts/backup.sh 등으로 주기적 백업 자동화
