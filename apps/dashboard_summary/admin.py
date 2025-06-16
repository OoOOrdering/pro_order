from django.contrib import admin

from .models import DashboardSummary


@admin.register(DashboardSummary)
class DashboardSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "total_orders",
        "total_revenue",
        "total_users",
        "total_reviews",
        "updated_at",
    )
    list_filter = ("date", "updated_at")
    search_fields = ("date",)
    readonly_fields = ("created_at", "updated_at")
