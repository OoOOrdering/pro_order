from rest_framework import serializers

from .models import Notification, NotificationToken, UserNotificationSetting


class NotificationSerializer(serializers.ModelSerializer):
    """
    알림 모델의 직렬화를 담당하는 시리얼라이저입니다.

    알림의 모든 필드를 JSON 형식으로 변환합니다.
    """

    class Meta:
        """
        시리얼라이저의 메타데이터를 정의합니다.

        모델과 직렬화할 필드를 지정합니다.
        """

        model = Notification
        fields = "__all__"


class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationToken
        fields = ("id", "user", "token", "provider", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "user", "created_at", "updated_at")


class UserNotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSetting
        fields = ("push_enabled", "email_enabled", "sms_enabled", "updated_at")
        read_only_fields = ("updated_at",)
