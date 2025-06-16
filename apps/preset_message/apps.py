from django.apps import AppConfig


class PresetMessageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.preset_message"
    verbose_name = "등록된 자동 메시지"
