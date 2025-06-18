from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    알림 모델의 관리자 인터페이스를 정의합니다.

    목록 표시, 필터링, 검색 기능을 제공합니다.
    """

    list_display = ("title", "user", "is_read", "created_at", "updated_at")
    list_filter = ("is_read", "created_at", "updated_at")
    search_fields = ("title", "content", "user__nickname")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
