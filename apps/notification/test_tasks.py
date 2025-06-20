from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.notification.models import Notification
from apps.notification.tasks import daily_cleanup, send_reminder_notification
from apps.user.models import User


@pytest.mark.django_db
def test_send_reminder_notification_creates_notification_and_sends_email():
    user = User.objects.create_user(email="reminder@example.com", password="testpass123!", nickname="reminderuser")
    title = "테스트 리마인더"
    content = "리마인더 알림 내용"
    with patch("utils.email.send_email_async.delay") as mock_email:
        send_reminder_notification(user.id, title, content)
        notification = Notification.objects.get(user=user, title=title)
        assert notification.content == content
        assert mock_email.called
        args, kwargs = mock_email.call_args
        assert title in args or title in kwargs.get("subject", "")
        assert content in args or content in kwargs.get("message", "")
        assert user.email in args or user.email in kwargs.get("to_email", "")


@pytest.mark.django_db
def test_daily_cleanup_deletes_old_notifications():
    user = User.objects.create_user(email="cleanup@example.com", password="testpass123!", nickname="cleanupuser")
    old_notification = Notification.objects.create(
        user=user,
        title="오래된 알림",
        content="30일 이상 지난 알림",
    )
    # created_at을 31일 전으로 강제 수정
    old_notification.created_at = timezone.now() - timezone.timedelta(days=31)
    old_notification.save(update_fields=["created_at"])

    recent_notification = Notification.objects.create(
        user=user,
        title="최근 알림",
        content="최근 알림",
    )
    daily_cleanup()
    assert not Notification.objects.filter(id=old_notification.id).exists()
    assert Notification.objects.filter(id=recent_notification.id).exists()
