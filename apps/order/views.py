import csv
from io import BytesIO

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from rest_framework import filters, generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.response import BaseResponseMixin

from .models import Order
from .serializers import (
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderRefundSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


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

    def get_queryset(self):
        # 예시: 필요한 필드만 조회
        qs = Order.objects.select_related("user", "payment").prefetch_related("items")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

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
        qs = Order.objects.select_related("user", "payment").prefetch_related("items")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return OrderUpdateSerializer
        return OrderSerializer

    def perform_update(self, serializer):
        # 관리자 또는 주문 소유자만 수정 가능
        if serializer.instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # 관리자 또는 주문 소유자만 삭제 가능
        if instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_destroy(instance)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAdminUser]  # 관리자만 환불 가능

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
