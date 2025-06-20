import csv
from io import BytesIO

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from reportlab.pdfgen import canvas
from rest_framework import filters, generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.user.permissions_role import IsAdmin
from utils.response import BaseResponseMixin

from .models import Order
from .serializers import (
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderRefundSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)
from .throttles import OrderRateThrottle


class OrderListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "payment_method", "payment_status"]
    search_fields = ["order_number", "shipping_name", "shipping_phone"]
    ordering_fields = ["created_at", "total_amount", "status"]
    throttle_classes = [UserRateThrottle, AnonRateThrottle, OrderRateThrottle]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        qs = Order.objects.select_related("user", "payment").prefetch_related("items")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="주문 목록 조회",
        operation_description="주문 목록을 조회합니다. (관리자는 전체, 일반 사용자는 본인 주문만 조회)",
        tags=["Order"],
        responses={
            200: openapi.Response("주문 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="주문 생성",
        operation_description="새로운 주문을 생성합니다.",
        tags=["Order"],
        responses={
            201: openapi.Response("주문이 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        order = serializer.instance
        output_serializer = OrderSerializer(order, context=self.get_serializer_context())
        self.logger.info(f"Order created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=output_serializer.data, message="주문이 생성되었습니다.", status=201)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        qs = Order.objects.select_related("user", "payment").prefetch_related("items")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="주문 상세 조회",
        operation_description="특정 주문의 상세 정보를 조회합니다.",
        tags=["Order"],
        responses={
            200: openapi.Response("주문 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "주문을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="주문 수정",
        operation_description="주문 정보를 수정합니다.",
        tags=["Order"],
        responses={
            200: openapi.Response("주문 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "주문을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="주문 부분 수정",
        operation_description="주문 정보를 부분 수정합니다.",
        tags=["Order"],
        responses={
            200: openapi.Response("주문 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "주문을 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="주문 삭제",
        operation_description="주문을 삭제합니다.",
        tags=["Order"],
        responses={
            204: openapi.Response("주문이 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "주문을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="주문 취소",
        operation_description="특정 주문을 취소합니다.",
    )
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {"detail": "이 주문을 취소할 권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = OrderCancelSerializer(order, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            order.status = Order.OrderStatus.CANCELLED
            order.cancelled_at = timezone.now()
            order.cancel_reason = serializer.validated_data["cancel_reason"]
            order.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"detail": "주문을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class OrderRefundView(APIView):
    permission_classes = [IsAdmin]  # 관리자만 환불 가능

    @swagger_auto_schema(
        operation_summary="주문 환불",
        operation_description="특정 주문을 환불 처리합니다. (관리자 전용)",
    )
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            serializer = OrderRefundSerializer(order, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            order.status = Order.OrderStatus.REFUNDED
            order.refunded_at = timezone.now()
            order.refund_reason = serializer.validated_data["refund_reason"]
            order.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"detail": "주문을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class OrderExportCSVView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="주문 내보내기 (CSV)",
        operation_description="주문 목록을 CSV 파일로 다운로드합니다.",
    )
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'

        writer = csv.writer(response)
        writer.writerow(["주문번호", "상태", "총 금액", "결제 방법", "배송 주소", "생성일"])

        orders = Order.objects.filter(user=request.user)
        for order in orders:
            writer.writerow(
                [
                    order.order_number,
                    order.status,
                    order.total_amount,
                    order.payment_method,
                    order.shipping_address,
                    order.created_at,
                ],
            )

        return response


class OrderExportPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="주문 내보내기 (PDF)",
        operation_description="특정 주문을 PDF 파일로 다운로드합니다.",
    )
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "주문을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        buffer = BytesIO()
        p = canvas.Canvas(buffer)

        # PDF 내용 작성
        p.drawString(100, 800, f"주문번호: {order.order_number}")
        p.drawString(100, 780, f"상태: {order.status}")
        p.drawString(100, 760, f"총 금액: {order.total_amount}")
        p.drawString(100, 740, f"결제 방법: {order.payment_method}")
        p.drawString(100, 720, f"배송 주소: {order.shipping_address}")
        p.drawString(100, 700, f"생성일: {order.created_at}")

        p.showPage()
        p.save()

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="order_{order.order_number}.pdf"'

        return response
