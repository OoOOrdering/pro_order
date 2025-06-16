from django.contrib import admin

from .models import CSPost


@admin.register(CSPost)
class CSPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "post_type",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("post_type", "status", "created_at")
    search_fields = ("title", "content", "author__nickname")
    readonly_fields = ("created_at", "updated_at")
