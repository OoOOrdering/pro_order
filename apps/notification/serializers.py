from rest_framework import serializers

from .models import Notification


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
