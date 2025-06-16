from django.contrib import admin

from .models import Progress


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "status",
        "updated_at",
        "estimated_completion_date",
        "actual_completion_date",
    )
    list_filter = ("status", "updated_at", "estimated_completion_date")
    search_fields = ("order__order_number", "notes")
    raw_id_fields = ("order", "last_updated_by")
    readonly_fields = ("created_at", "updated_at")
