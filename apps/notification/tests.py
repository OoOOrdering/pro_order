from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User

from .models import Notification


@pytest.fixture
def api_client():
    """API 클라이언트 픽스처를 생성합니다."""
    return APIClient()


@pytest.fixture
def create_user():
    """사용자 생성 픽스처를 생성합니다."""

    def _create_user(email, password, is_staff=False, **kwargs):
        return User.objects.create_user(email=email, password=password, is_staff=is_staff, is_active=True, **kwargs)

    return _create_user


@pytest.fixture
def authenticate_client(api_client, create_user):
    """인증된 API 클라이언트 픽스처를 생성합니다."""

    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            user = create_user(
                email=f"test_user_{timezone.now().timestamp()}@example.com",
                password="testpass123!",
                is_staff=is_staff,
            )
        login_url = reverse("user:token_login")
        response = api_client.post(login_url, {"email": user.email, "password": "testpass123!"})
        access_token = response.data["data"]["access_token"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return user

    return _authenticate_client


@pytest.mark.django_db
class TestNotificationAPI:
    """
    알림 API에 대한 테스트 클래스입니다.

    알림 생성, 조회, 수정, 삭제, 읽음 표시 등의 기능을 테스트합니다.
    """

    def test_create_notification_by_admin(self, api_client, authenticate_client, create_user):
        """관리자가 알림을 생성할 수 있는지 테스트합니다."""
        admin_user = authenticate_client(is_staff=True)
        normal_user = create_user("notify_target@example.com", "pass123!")
        url = reverse("notification-list-create")
        data = {
            "user": normal_user.id,
            "title": "Admin Created Notification",
            "content": "This notification is for a specific user",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Notification.objects.count() == 1  # Assuming no other notifications exist initially
        assert Notification.objects.filter(user=normal_user).exists()

    def test_create_notification_by_normal_user_fails(self, api_client, authenticate_client, create_user):
        """일반 사용자가 알림을 생성할 수 없는지 테스트합니다."""
        normal_user = authenticate_client(is_staff=False)
        other_user = create_user("another_target@example.com", "pass123!")
        url = reverse("notification-list-create")
        data = {
            "user": other_user.id,
            "title": "Normal User Notification",
            "content": "This should fail",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Notification.objects.count() == 0  # No notification should be created

    def test_get_notification_list_by_admin(self, api_client, authenticate_client, create_user):
        """관리자가 모든 알림 목록을 조회할 수 있는지 테스트합니다."""
        admin_user = authenticate_client(is_staff=True)
        user1 = create_user("user1_notif@example.com", "pass1")
        user2 = create_user("user2_notif@example.com", "pass2")
        Notification.objects.create(user=user1, title="Notif 1", content="Content 1")
        Notification.objects.create(user=user2, title="Notif 2", content="Content 2")
        url = reverse("notification-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_notification_list_by_normal_user_sees_only_own_notifications(
        self,
        api_client,
        authenticate_client,
        create_user,
    ):
        """일반 사용자가 자신의 알림만 조회할 수 있는지 테스트합니다."""
        normal_user = authenticate_client()
        other_user = create_user("other_notif_user@example.com", "pass")
        my_notification = Notification.objects.create(user=normal_user, title="My Notif", content="My content")
        other_notification = Notification.objects.create(user=other_user, title="Other Notif", content="Other content")
        url = reverse("notification-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == my_notification.pk

    def test_get_notification_detail_by_owner(self, api_client, authenticate_client):
        """알림 소유자가 자신의 알림 상세 정보를 조회할 수 있는지 테스트합니다."""
        user = authenticate_client()
        notification = Notification.objects.create(user=user, title="Detail Notif", content="Detail Content")
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == notification.pk

    def test_get_notification_detail_by_admin(self, api_client, authenticate_client, create_user):
        """관리자가 모든 알림의 상세 정보를 조회할 수 있는지 테스트합니다."""
        admin_user = authenticate_client(is_staff=True)
        normal_user = create_user("target_user_detail@example.com", "pass")
        notification = Notification.objects.create(
            user=normal_user,
            title="Admin Access Notif",
            content="Admin Content",
        )
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == notification.pk

    def test_get_notification_detail_by_non_owner_fails(self, api_client, authenticate_client, create_user):
        """알림 소유자가 아닌 사용자가 알림 상세 정보를 조회할 수 없는지 테스트합니다."""
        normal_user = authenticate_client()
        other_user = create_user("other_user_detail@example.com", "pass")
        notification = Notification.objects.create(
            user=other_user,
            title="Restricted Notif",
            content="Restricted Content",
        )
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Should be 404 because queryset filters

    def test_update_notification_by_owner(self, api_client, authenticate_client):
        """알림 소유자가 자신의 알림을 수정할 수 있는지 테스트합니다."""
        user = authenticate_client()
        notification = Notification.objects.create(user=user, title="Updatable Notif", content="Original Content")
        url = reverse("notification-detail", args=[notification.pk])
        updated_data = {"content": "Updated Content"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.content == "Updated Content"

    def test_update_notification_by_admin(self, api_client, authenticate_client, create_user):
        """관리자가 모든 알림을 수정할 수 있는지 테스트합니다."""
        admin_user = authenticate_client(is_staff=True)
        normal_user = create_user("update_target_user@example.com", "pass")
        notification = Notification.objects.create(
            user=normal_user,
            title="Admin Updatable Notif",
            content="Original Content",
        )
        url = reverse("notification-detail", args=[notification.pk])
        updated_data = {"content": "Admin Updated Content"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.content == "Admin Updated Content"

    def test_update_notification_by_non_owner_fails(self, api_client, authenticate_client, create_user):
        """알림 소유자가 아닌 사용자가 알림을 수정할 수 없는지 테스트합니다."""
        normal_user = authenticate_client()
        other_user = create_user("other_user_update@example.com", "pass")
        notification = Notification.objects.create(
            user=other_user,
            title="Restricted Update Notif",
            content="Original Content",
        )
        url = reverse("notification-detail", args=[notification.pk])
        updated_data = {"content": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Should be 404 because queryset filters

    def test_delete_notification_by_owner(self, api_client, authenticate_client):
        """알림 소유자가 자신의 알림을 삭제할 수 있는지 테스트합니다."""
        user = authenticate_client()
        notification = Notification.objects.create(user=user, title="Deletable Notif", content="Content")
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(pk=notification.pk).exists()

    def test_delete_notification_by_admin(self, api_client, authenticate_client, create_user):
        """관리자가 모든 알림을 삭제할 수 있는지 테스트합니다."""
        admin_user = authenticate_client(is_staff=True)
        normal_user = create_user("delete_target_user@example.com", "pass")
        notification = Notification.objects.create(user=normal_user, title="Admin Deletable Notif", content="Content")
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(pk=notification.pk).exists()

    def test_delete_notification_by_non_owner_fails(self, api_client, authenticate_client, create_user):
        """알림 소유자가 아닌 사용자가 알림을 삭제할 수 없는지 테스트합니다."""
        normal_user = authenticate_client()
        other_user = create_user("other_user_delete@example.com", "pass")
        notification = Notification.objects.create(user=other_user, title="Restricted Delete Notif", content="Content")
        url = reverse("notification-detail", args=[notification.pk])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Should be 404 because queryset filters

    def test_mark_notification_as_read_by_owner(self, api_client, authenticate_client):
        """알림 소유자가 자신의 알림을 읽음 상태로 표시할 수 있는지 테스트합니다."""
        user = authenticate_client()
        notification = Notification.objects.create(user=user, title="Unread Notif", content="Content", is_read=False)
        url = reverse("notification-mark-as-read", args=[notification.pk])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_notification_as_read_by_non_owner_fails(self, api_client, authenticate_client, create_user):
        """알림 소유자가 아닌 사용자가 알림을 읽음 상태로 표시할 수 없는지 테스트합니다."""
        normal_user = authenticate_client()
        other_user = create_user("other_user_mark_read@example.com", "pass")
        notification = Notification.objects.create(
            user=other_user,
            title="Other User Unread Notif",
            content="Content",
            is_read=False,
        )
        url = reverse("notification-mark-as-read", args=[notification.pk])
        response = api_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # Due to queryset filter in view

    def test_unread_notification_list(self, api_client, authenticate_client):
        """읽지 않은 알림 목록을 조회할 수 있는지 테스트합니다."""
        user = authenticate_client()
        # Create some notifications
        Notification.objects.create(user=user, title="Unread 1", content="Content 1", is_read=False)
        Notification.objects.create(user=user, title="Unread 2", content="Content 2", is_read=False)
        Notification.objects.create(user=user, title="Read 1", content="Content 3", is_read=True)

        url = reverse("notification-unread-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert all(not item["is_read"] for item in response.data["results"])

    def test_notification_unread_count(self, api_client, authenticate_client):
        """읽지 않은 알림의 개수를 조회할 수 있는지 테스트합니다."""
        user = authenticate_client()
        # Create some notifications
        Notification.objects.create(user=user, title="Unread 1", content="Content 1", is_read=False)
        Notification.objects.create(user=user, title="Unread 2", content="Content 2", is_read=False)
        Notification.objects.create(user=user, title="Read 1", content="Content 3", is_read=True)

        url = reverse("notification-unread-count")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["unread_count"] == 2

    def test_notification_list_filter_by_is_read(self, api_client, authenticate_client):
        """알림 목록을 읽음 상태로 필터링할 수 있는지 테스트합니다."""
        user = authenticate_client()
        # Create notifications with different read statuses
        Notification.objects.create(user=user, title="Unread 1", content="Content 1", is_read=False)
        Notification.objects.create(user=user, title="Read 1", content="Content 2", is_read=True)

        url = reverse("notification-list-create")
        response = api_client.get(url, {"is_read": "false"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert not response.data["results"][0]["is_read"]

    def test_notification_list_search(self, api_client, authenticate_client):
        """알림 목록을 검색할 수 있는지 테스트합니다."""
        user = authenticate_client()
        # Create notifications with different titles
        Notification.objects.create(user=user, title="Important Notice", content="Content 1")
        Notification.objects.create(user=user, title="Regular Update", content="Content 2")

        url = reverse("notification-list-create")
        response = api_client.get(url, {"search": "Important"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "Important" in response.data["results"][0]["title"]

    def test_notification_list_sort_by_created_at(self, api_client, authenticate_client):
        """알림 목록을 생성일시 기준으로 정렬할 수 있는지 테스트합니다."""
        user = authenticate_client()
        # Create notifications with different timestamps
        now = timezone.now()
        Notification.objects.create(
            user=user,
            title="Older",
            content="Content 1",
            created_at=now - timedelta(hours=1),
        )
        Notification.objects.create(user=user, title="Newer", content="Content 2", created_at=now)

        url = reverse("notification-list-create")
        response = api_client.get(url, {"ordering": "-created_at"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["title"] == "Newer"
