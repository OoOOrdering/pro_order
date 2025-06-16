from django.contrib import admin

from .models import PresetMessage


@admin.register(PresetMessage)
class PresetMessageAdmin(admin.ModelAdmin):
    list_display = ("title", "content", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("created_at", "updated_at")
