from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import OrderStatusLog
from .serializers import OrderStatusLogCreateSerializer, OrderStatusLogSerializer


class OrderStatusLogListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderStatusLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["previous_status", "new_status", "changed_by"]
    search_fields = ["order__order_number", "reason", "memo"]
    ordering_fields = ["created_at", "previous_status", "new_status"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderStatusLog.objects.all()
        return OrderStatusLog.objects.filter(order__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderStatusLogCreateSerializer
        return OrderStatusLogSerializer

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("주문 상태 로그를 생성할 권한이 없습니다.")
        serializer.save(changed_by=self.request.user)


class OrderStatusLogDetailView(generics.RetrieveAPIView):
    serializer_class = OrderStatusLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderStatusLog.objects.all()
        return OrderStatusLog.objects.filter(order__user=self.request.user)
