from django.contrib import admin

from .models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "review", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__nickname", "review__pk")
    raw_id_fields = ("user", "review")
