from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("chat_room", "sender", "content", "sent_at", "is_read")
    list_filter = ("is_read", "sent_at", "chat_room", "sender")
    search_fields = ("content", "chat_room__pk", "sender__nickname")
    raw_id_fields = ("chat_room", "sender")
    readonly_fields = ("sent_at",)
