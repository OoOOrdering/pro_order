from django.contrib import admin

from .models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "created_at")
    list_filter = ("created_at", "content_type")
    search_fields = ("user__nickname", "object_id")
    raw_id_fields = ("user",)
