from django.contrib import admin

from .models import Progress


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "last_updated")
    list_filter = ("status", "last_updated")
    search_fields = ("order__pk", "status")
    raw_id_fields = ("order",)
