from django.contrib import admin

from .models import DailyAnalytics, EventLog


@admin.register(DailyAnalytics)
class DailyAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "page_views",
        "unique_visitors",
        "conversion_rate",
        "average_order_value",
    )
    list_filter = ("date",)
    search_fields = ("date",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "event_name",
        "event_type",
        "user",
        "object_type",
        "object_id",
    )
    list_filter = ("event_type", "user", "timestamp")
    search_fields = ("event_name", "metadata", "user__email")
    readonly_fields = ("timestamp",)
