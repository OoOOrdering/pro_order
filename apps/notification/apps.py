from django.apps import AppConfig


class NotificationConfig(AppConfig):
    """알림 앱의 설정을 정의합니다.

    앱의 기본 설정과 메타데이터를 관리합니다.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notification"
    verbose_name = "알림"
