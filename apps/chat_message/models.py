from django.db import models

from apps.chat_room.models import ChatRoom
from apps.user.models import User


class ChatMessage(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    message_type = models.CharField(
        max_length=20,
        choices=(
            ("text", "Text"),
            ("image", "Image"),
            ("file", "File"),
            ("system", "System"),  # 시스템 메시지 (예: 사용자 입장/퇴장)
        ),
        default="text",
    )
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)

    class Meta:
        ordering = ["timestamp"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self):
        return f"Message from {self.sender.nickname} in {self.chat_room.name}"
