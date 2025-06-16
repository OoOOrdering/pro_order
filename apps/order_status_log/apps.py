from django.apps import AppConfig


class OrderStatusLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.order_status_log"
    verbose_name = "주문 상태 기록"
