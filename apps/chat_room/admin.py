from django.contrib import admin

from .models import ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "room_type", "created_by", "created_at")
    list_filter = ("created_at", "room_type")
    search_fields = ("name", "created_by__nickname")
    raw_id_fields = ("created_by", "participants")
