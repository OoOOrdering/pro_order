from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response

from .models import OrderStatusLog
from .serializers import OrderStatusLogCreateSerializer, OrderStatusLogListSerializer


class OrderStatusLogListCreateView(generics.ListCreateAPIView):
    serializer_class = OrderStatusLogCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["previous_status", "new_status", "changed_by"]
    search_fields = ["order__order_number", "reason", "memo"]
    ordering_fields = ["created_at", "previous_status", "new_status"]

    queryset = OrderStatusLog.objects.select_related("order", "changed_by").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderStatusLogListSerializer
        return super().get_serializer_class()

    def post(self, request, *args, **kwargs):
        return Response(
            {"detail": "주문 상태 로그는 직접 생성할 수 없습니다. 주문 상태 변경을 통해 자동 생성됩니다."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class OrderStatusLogDetailView(generics.RetrieveAPIView):
    serializer_class = OrderStatusLogListSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    queryset = OrderStatusLog.objects.select_related("order", "changed_by").all()
