from django.core.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
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

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderStatusLog.objects.none()
        return OrderStatusLog.objects.select_related("order", "changed_by").all()

    @swagger_auto_schema(
        operation_summary="주문 상태 변경 이력 목록 조회",
        operation_description="주문 상태 변경 이력의 전체 목록을 조회합니다. 필터, 검색, 정렬이 가능합니다.",
        tags=["OrderStatusLog"],
        responses={
            200: openapi.Response("주문 상태 변경 이력 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="주문 상태 변경 이력 직접 생성 불가",
        operation_description="주문 상태 변경 이력은 직접 생성할 수 없습니다. 주문 상태 변경 시 자동으로 생성됩니다.",
        tags=["OrderStatusLog"],
        responses={
            405: openapi.Response(
                "주문 상태 변경 이력은 직접 생성할 수 없습니다. 주문 상태 변경 시 자동으로 생성됩니다."
            ),
            401: "인증되지 않은 사용자입니다.",
        },
    )
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

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OrderStatusLog.objects.none()
        return OrderStatusLog.objects.select_related("order", "changed_by").all()

    @swagger_auto_schema(
        operation_summary="주문 상태 변경 이력 상세 조회",
        operation_description="특정 주문 상태 변경 이력의 상세 정보를 조회합니다.",
        tags=["OrderStatusLog"],
        responses={
            200: openapi.Response("주문 상태 변경 이력 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            404: "주문 상태 변경 이력을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
