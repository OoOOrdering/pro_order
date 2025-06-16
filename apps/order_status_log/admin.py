from django.contrib import admin

from .models import OrderStatusLog


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "previous_status",
        "new_status",
        "changed_by",
        "created_at",
    )
    list_filter = ("previous_status", "new_status", "created_at")
    search_fields = ("order__order_number", "changed_by__nickname", "reason")
    raw_id_fields = ("order", "changed_by")
    readonly_fields = ("created_at",)
