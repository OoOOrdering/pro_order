from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "reviewer",
        "rating",
        "is_public",
        "created_at",
        "updated_at",
    )
    list_filter = ("rating", "is_public", "created_at")
    search_fields = (
        "order__order_number",
        "reviewer__nickname",
        "comment",
    )
    raw_id_fields = ("order", "reviewer")
    readonly_fields = ("created_at", "updated_at")
