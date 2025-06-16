from django.contrib import admin

from .models import DashboardSummary


@admin.register(DashboardSummary)
class DashboardSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_orders",
        "total_revenue",
        "new_users_today",
        "active_chat_rooms",
        "unresolved_cs_posts",
        "last_updated",
    )
    list_filter = ("last_updated",)
    search_fields = ("user__nickname",)
    readonly_fields = ("last_updated",)
