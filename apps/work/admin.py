from django.contrib import admin

from .models import Work


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("title", "description", "order__pk")
    raw_id_fields = ("order",)
    readonly_fields = ("created_at", "updated_at")
