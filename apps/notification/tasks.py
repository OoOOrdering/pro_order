from celery import shared_task
from django.utils import timezone

from .models import Notification


@shared_task
def send_reminder_notification(user_id, title, content):
    """
    특정 시점에 사용자에게 알림을 생성하고 이메일을 전송하는 리마인더용 태스크.
    """
    from apps.user.models import User
    from utils.email import send_email_async

    user = User.objects.get(pk=user_id)
    notification = Notification.objects.create(user=user, title=title, content=content)
    if user.email:
        send_email_async.delay(subject=title, message=content, to_email=user.email)


@shared_task
def daily_cleanup():
    """
    오래된 알림(30일 초과) 자동 삭제. (예약 작업 예시)
    """
    threshold = timezone.now() - timezone.timedelta(days=30)
    Notification.objects.filter(created_at__lt=threshold).delete()
