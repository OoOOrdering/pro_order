from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.order.models import Order
from apps.user.models import User


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    previous_status = models.CharField(_("이전 상태"), max_length=20)
    new_status = models.CharField(_("새 상태"), max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="status_changes")
    reason = models.TextField(_("변경 사유"), blank=True)
    memo = models.TextField(_("메모"), blank=True)
    created_at = models.DateTimeField(_("생성일"), auto_now_add=True)

    class Meta:
        verbose_name = _("주문 상태 로그")
        verbose_name_plural = _("주문 상태 로그들")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.previous_status} -> {self.new_status}"

    def save(self, *args, **kwargs):
        # 상태 변경 시 알림 생성
        from apps.notification.models import Notification

        super().save(*args, **kwargs)

        # 주문 상태 변경 알림 생성
        Notification.objects.create(
            user=self.order.user,
            title="주문 상태 변경",
            message=f"주문 {self.order.order_number}의 상태가 {self.previous_status}에서 {self.new_status}로 변경되었습니다.",
            notification_type="ORDER_STATUS_CHANGE",
        )
