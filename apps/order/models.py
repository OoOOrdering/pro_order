from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.user.models import User


class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = "PENDING", _("대기중")
        PROCESSING = "PROCESSING", _("처리중")
        COMPLETED = "COMPLETED", _("완료")
        CANCELLED = "CANCELLED", _("취소")
        REFUNDED = "REFUNDED", _("환불")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(_("주문번호"), max_length=50, unique=True)
    status = models.CharField(
        _("상태"),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    total_amount = models.DecimalField(_("총 금액"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_("결제 방법"), max_length=50)
    payment_status = models.CharField(_("결제 상태"), max_length=20)
    payment_id = models.CharField(_("결제 ID"), max_length=100, blank=True)
    shipping_address = models.TextField(_("배송 주소"))
    shipping_phone = models.CharField(_("배송 연락처"), max_length=20)
    shipping_name = models.CharField(_("수령인"), max_length=50)
    shipping_memo = models.TextField(_("배송 메모"), blank=True)
    created_at = models.DateTimeField(_("생성일"), auto_now_add=True)
    updated_at = models.DateTimeField(_("수정일"), auto_now=True)
    cancelled_at = models.DateTimeField(_("취소일"), null=True, blank=True)
    refunded_at = models.DateTimeField(_("환불일"), null=True, blank=True)
    cancel_reason = models.TextField(_("취소 사유"), blank=True)
    refund_reason = models.TextField(_("환불 사유"), blank=True)

    class Meta:
        verbose_name = _("주문")
        verbose_name_plural = _("주문들")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} - {self.user.email}"

    def save(self, *args, **kwargs):
        status_changed = False
        if self.pk is not None:
            old_instance = Order.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                status_changed = True
                from apps.order_status_log.models import OrderStatusLog

                OrderStatusLog.objects.create(
                    order=self,
                    previous_status=old_instance.status,
                    new_status=self.status,
                    reason="상태 변경",
                    changed_by=self.user,
                )
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_name = models.CharField(_("상품명"), max_length=200)
    quantity = models.PositiveIntegerField(_("수량"))
    price = models.DecimalField(_("가격"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_("생성일"), auto_now_add=True)

    class Meta:
        verbose_name = _("주문 상품")
        verbose_name_plural = _("주문 상품들")

    def __str__(self):
        return f"{self.product_name} - {self.order.order_number}"


class OrderPayment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    payment_method = models.CharField(_("결제 방법"), max_length=50)
    payment_id = models.CharField(_("결제 ID"), max_length=100)
    amount = models.DecimalField(_("결제 금액"), max_digits=10, decimal_places=2)
    status = models.CharField(_("결제 상태"), max_length=20)
    created_at = models.DateTimeField(_("생성일"), auto_now_add=True)
    updated_at = models.DateTimeField(_("수정일"), auto_now=True)

    class Meta:
        verbose_name = _("주문 결제")
        verbose_name_plural = _("주문 결제들")

    def __str__(self):
        return f"{self.order.order_number} - {self.payment_method}"
