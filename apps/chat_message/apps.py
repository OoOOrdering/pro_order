from django.apps import AppConfig


class ChatMessageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.chat_message"
    verbose_name = "채팅 메시지"
