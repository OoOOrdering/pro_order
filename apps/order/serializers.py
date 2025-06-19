from rest_framework import serializers

from apps.user.serializers import UserSerializer  # UserSerializer가 필요하다고 가정
from utils.serializers import BaseSerializer

from .models import Order, OrderItem, OrderPayment


class OrderItemSerializer(BaseSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        read_only_fields = ("order",)


class OrderPaymentSerializer(BaseSerializer):
    class Meta:
        model = OrderPayment
        fields = "__all__"


class OrderSerializer(BaseSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    payment = OrderPaymentSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "user",
            "order_number",
            "status",
            "status_display",
            "total_amount",
            "payment_method",
            "payment_status",
            "payment_id",
            "shipping_address",
            "shipping_phone",
            "shipping_name",
            "shipping_memo",
            "created_at",
            "updated_at",
            "cancelled_at",
            "refunded_at",
            "cancel_reason",
            "refund_reason",
            "items",
            "payment",
        )
        read_only_fields = (
            "order_number",
            "status",
            "payment_status",
            "payment_id",
            "created_at",
            "updated_at",
            "cancelled_at",
            "refunded_at",
        )


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            "shipping_address",
            "shipping_phone",
            "shipping_name",
            "shipping_memo",
            "items",
            "payment_method",
            "payment_id",
            "total_amount",
        )

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "shipping_address",
            "shipping_phone",
            "shipping_name",
            "shipping_memo",
            "status",
        )
        read_only_fields = ("status",)


class OrderCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("cancel_reason",)

    def validate(self, data):
        if self.instance.status in [
            Order.OrderStatus.COMPLETED,
            Order.OrderStatus.CANCELLED,
            Order.OrderStatus.REFUNDED,
        ]:
            raise serializers.ValidationError("이미 완료, 취소 또는 환불된 주문은 취소할 수 없습니다.")
        if not data.get("cancel_reason"):
            raise serializers.ValidationError("취소 사유는 필수입니다.")
        return data


class OrderRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("refund_reason",)

    def validate(self, data):
        if self.instance.status != Order.OrderStatus.CANCELLED:
            raise serializers.ValidationError("취소된 주문만 환불할 수 있습니다.")
        if not data.get("refund_reason"):
            raise serializers.ValidationError("환불 사유는 필수입니다.")
        return data


class OrderFilterSerializer(serializers.Serializer):
    status = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    search = serializers.CharField(required=False)
