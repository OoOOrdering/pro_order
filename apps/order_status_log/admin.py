from django.contrib import admin

from .models import OrderStatusLog


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ("order", "old_status", "new_status", "changed_at", "user")
    list_filter = ("old_status", "new_status", "changed_at")
    search_fields = ("order__order_number", "user__nickname", "reason")
    raw_id_fields = ("order", "user")
    readonly_fields = ("changed_at",)
