from django.contrib import admin

from .models import ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("pk", "user1", "user2", "created_at", "last_message_at")
    list_filter = ("created_at", "last_message_at")
    search_fields = ("user1__nickname", "user2__nickname")
    raw_id_fields = ("user1", "user2")
