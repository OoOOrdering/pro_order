from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "user", "rating", "created_at")
    list_filter = ("rating", "created_at", "updated_at")
    search_fields = ("content", "order__pk", "user__nickname")
    raw_id_fields = ("order", "user")
    readonly_fields = ("created_at", "updated_at")
