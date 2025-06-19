from rest_framework import serializers

from .models import OrderStatusLog


class OrderStatusLogListSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)
    changed_by_nickname = serializers.CharField(source="changed_by.nickname", read_only=True)
    order_title = serializers.CharField(source="order.title", read_only=True)
    # 테스트에서 기대하는 'id', 'previous_status', 'new_status', 'changed_by', 'reason', 'memo', 'created_at' 모두 포함되어 있음
    # 만약 추가 필드가 필요하면 아래에 추가

    class Meta:
        model = OrderStatusLog
        fields = (
            "id",
            "order",
            "order_title",
            "previous_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "changed_by_nickname",
            "reason",
            "memo",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = (
            "id",
            "order",
            "previous_status",
            "new_status",
            "changed_by",
            "changed_by_email",
            "reason",
            "memo",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class OrderStatusLogCreateSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = OrderStatusLog
        fields = ("order", "new_status", "reason", "memo", "changed_by_email")

    def validate(self, attrs):
        order = attrs["order"]
        new_status = attrs["new_status"]

        # 현재 상태와 새로운 상태가 다른지 확인
        if order.status == new_status:
            raise serializers.ValidationError("새로운 상태가 현재 상태와 같습니다.")

        return attrs

    def create(self, validated_data):
        order = validated_data["order"]
        previous_status = order.status
        new_status = validated_data["new_status"]

        # 주문 상태 업데이트
        order.status = new_status
        order.save()

        # 상태 변경 로그 생성
        log = OrderStatusLog.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=self.context["request"].user,
            reason=validated_data.get("reason", ""),
            memo=validated_data.get("memo", ""),
        )

        return log
