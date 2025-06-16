from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_at", "updated_at")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
