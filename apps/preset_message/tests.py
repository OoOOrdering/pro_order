from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.preset_message.models import PresetMessage


@pytest.mark.django_db
class TestPresetMessageAPI:
    def test_create_preset_message(self, authenticated_client):
        client, user = authenticated_client()
        url = reverse("preset_message:preset-message-list-create")
        data = {
            "title": "Greeting Message",
            "content": "Hello, how can I help you?",
            "is_active": True,
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "Greeting Message"
        assert response.data["user"] == user.id

    def test_get_preset_message_list(self, authenticated_client, create_preset_message, create_user):
        client, user1 = authenticated_client()
        user2 = create_user(is_staff=False)

        # Create messages for different users
        create_preset_message(user=user1, title="User1 Message 1")
        create_preset_message(user=user1, title="User1 Message 2")
        create_preset_message(user=user2, title="User2 Message 1")
        create_preset_message(user=None, title="Global Message")

        url = reverse("preset_message:preset-message-list-create")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3  # 자신의 메시지 2개 + 글로벌 메시지 1개

    def test_filter_preset_message_by_active_status(self, authenticated_client, create_preset_message):
        client, user = authenticated_client()
        create_preset_message(user=user, title="Active Message", is_active=True)
        create_preset_message(user=user, title="Inactive Message", is_active=False)

        url = reverse("preset_message:preset-message-list-create") + "?is_active=true"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Active Message"

    def test_filter_preset_message_by_date_range(self, authenticated_client, create_preset_message):
        client, user = authenticated_client()
        # 과거 메시지 생성 후 created_at을 수동으로 수정 (7일 전 UTC 00:00:00)
        import pytz
        from django.utils import timezone

        utc = pytz.UTC
        past_date = (
            (timezone.now() - timedelta(days=7)).astimezone(utc).replace(hour=0, minute=0, second=0, microsecond=0)
        )
        past_message = create_preset_message(user=user, title="Past Message")
        past_message.created_at = past_date
        past_message.save(update_fields=["created_at"])

        # 최근 메시지는 오늘 날짜
        recent_message = create_preset_message(user=user, title="Recent Message")

        today = timezone.now().date()
        url = reverse("preset_message:preset-message-list-create") + f"?created_at__gte={today}&created_at__lte={today}"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        titles = [item["title"] for item in response.data["results"]]
        assert "Recent Message" in titles

    def test_preset_message_detail(self, authenticated_client, create_preset_message):
        client, user = authenticated_client()
        message = create_preset_message(user=user)

        url = reverse("preset_message:preset-message-detail", args=[message.pk])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == message.pk
        assert response.data["title"] == message.title
        assert response.data["user"] == user.id

    def test_update_preset_message(self, authenticated_client, create_preset_message):
        client, user = authenticated_client()
        message = create_preset_message(user=user)

        url = reverse("preset_message:preset-message-detail", args=[message.pk])
        data = {"title": "Updated Title", "content": "Updated content", "is_active": False}
        response = client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Updated Title"
        assert response.data["content"] == "Updated content"
        assert response.data["is_active"] == False

    def test_delete_preset_message(self, authenticated_client, create_preset_message):
        client, user = authenticated_client()
        message = create_preset_message(user=user)

        url = reverse("preset_message:preset-message-detail", args=[message.pk])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PresetMessage.objects.filter(pk=message.pk).exists()
