from django.contrib import admin

from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_at", "updated_at")
    search_fields = ("question", "answer")
    readonly_fields = ("created_at", "updated_at")
