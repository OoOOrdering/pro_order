from django.db import models

from apps.notification.models import Notification
from apps.order.models import Order


class OrderStatusLog(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_logs",
        verbose_name="주문",
    )
    previous_status = models.CharField(
        max_length=20,
        choices=Order.OrderStatus.choices,
        verbose_name="이전 상태",
    )
    new_status = models.CharField(
        max_length=20,
        choices=Order.OrderStatus.choices,
        verbose_name="새 상태",
    )
    reason = models.TextField(verbose_name="변경 사유")
    memo = models.TextField(verbose_name="메모", blank=True)
    changed_by = models.ForeignKey(
        "user.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_status_logs",
        verbose_name="변경자",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "주문 상태 로그"
        verbose_name_plural = "주문 상태 로그"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # 주문 상태 변경 시 알림 생성
        title = "주문 상태 변경 알림"
        content = (
            f"주문 {self.order.order_number}의 상태가 {self.previous_status}에서 {self.new_status}로 변경되었습니다."
        )

        Notification.objects.create(user=self.order.user, title=title, content=content)
