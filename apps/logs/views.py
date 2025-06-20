from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.permissions_role import IsAdmin

from .models import ActionLog
from .serializers import ActionLogSerializer


class ActionLogListView(generics.ListAPIView):
    serializer_class = ActionLogSerializer
    permission_classes = [IsAdmin]
    queryset = ActionLog.objects.all().order_by("-created_at")
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["action", "user", "created_at"]
    search_fields = ["detail"]
    ordering_fields = ["created_at", "action", "user"]


class ActionLogStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        # action별 카운트
        action_counts = ActionLog.objects.values("action").annotate(count=Count("id")).order_by("-count")
        # 최근 7일간 일별 카운트
        today = timezone.now().date()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        daily_counts = []
        for day in last_7_days:
            count = ActionLog.objects.filter(created_at__date=day).count()
            daily_counts.append({"date": day, "count": count})
        return Response({"action_counts": list(action_counts), "daily_counts": daily_counts})
