from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

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


class EventLogListCreateView(generics.ListCreateAPIView):
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
        # 관리자는 모든 이벤트 로그 조회, 일반 사용자는 자신의 이벤트 로그만 조회
        if self.request.user.is_staff:
            queryset = EventLog.objects.all()
        else:
            queryset = EventLog.objects.filter(user=self.request.user)

        start_timestamp = self.request.query_params.get("start_timestamp")
        end_timestamp = self.request.query_params.get("end_timestamp")

        if start_timestamp:
            queryset = queryset.filter(timestamp__gte=start_timestamp)
        if end_timestamp:
            queryset = queryset.filter(timestamp__lte=end_timestamp)

        return queryset

    def perform_create(self, serializer):
        # 이벤트 로그 생성 시 요청한 사용자를 자동으로 할당
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save(user=None)  # 익명 사용자일 경우 user=None


class EventLogDetailView(generics.RetrieveAPIView):
    queryset = EventLog.objects.all()
    serializer_class = EventLogSerializer
    permission_classes = [permissions.IsAdminUser]  # 관리자만 접근 가능
    lookup_field = "pk"


class AnalyticsListView(generics.ListAPIView):
    queryset = DailyAnalytics.objects.all()
    serializer_class = DailyAnalyticsSerializer
    filterset_fields = ["month"]  # 월별 필터링 추가


class AnalyticsDetailView(generics.RetrieveAPIView):
    queryset = DailyAnalytics.objects.all()
    serializer_class = DailyAnalyticsSerializer
    lookup_field = "month"  # 월로 조회
