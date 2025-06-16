from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.order_status_log.models import OrderStatusLog

from .models import Order


@receiver(post_save, sender=Order)
def create_order_status_log(sender, instance, **kwargs):
    """주문 상태가 변경될 때 로그를 생성합니다."""
    if instance.pk:  # 새로운 인스턴스가 아닌 경우에만
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                OrderStatusLog.objects.create(
                    order=instance,
                    previous_status=old_instance.status,
                    new_status=instance.status,
                )
        except Order.DoesNotExist:
            pass
