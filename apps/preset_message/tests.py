from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.preset_message.models import PresetMessage
from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email, password, is_staff=False, **kwargs):
        return User.objects.create_user(email=email, password=password, is_staff=is_staff, is_active=True, **kwargs)

    return _create_user


@pytest.fixture
def authenticate_client(api_client, create_user):
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


@pytest.fixture
def create_preset_message(db, create_user):
    def _create_preset_message(user=None, **kwargs):
        if user is None:
            user = create_user("default_preset_user@example.com", "testpass123!")
        return PresetMessage.objects.create(
            title=f"Preset Title {timezone.now().timestamp()}",
            content=f"Preset Content {timezone.now().timestamp()}",
            user=user,
            **kwargs,
        )

    return _create_preset_message


@pytest.mark.django_db
class TestPresetMessageAPI:
    def test_create_preset_message(self, api_client, authenticate_client):
        user = authenticate_client()
        url = reverse("preset_message:preset-message-list-create")
        data = {
            "title": "Greeting Message",
            "content": "Hello, how can I help you?",
            "is_active": True,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert PresetMessage.objects.count() == 1
        assert response.data["title"] == "Greeting Message"
        assert response.data["user"] == user.pk

    def test_get_preset_message_list(self, api_client, authenticate_client, create_preset_message, create_user):
        user1 = authenticate_client()
        user2 = create_user("user2@example.com", "testpass123!")
        create_preset_message(user=user1, title="User1 Message 1")
        create_preset_message(user=user1, title="User1 Message 2")
        create_preset_message(user=user2, title="User2 Message 1")
        create_preset_message(user=None, title="Global Message")

        url = reverse("preset_message:preset-message-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_filter_preset_message_by_active_status(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        create_preset_message(user=user, title="Active Message", is_active=True)
        create_preset_message(user=user, title="Inactive Message", is_active=False)

        url = reverse("preset_message:preset-message-list-create") + "?is_active=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Active Message"

    def test_filter_preset_message_by_date_range(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        message = create_preset_message(user=user, title="Date Range Test", created_at=today)

        url = (
            reverse("preset_message:preset-message-list-create")
            + f"?created_at__gte={yesterday.date()}&created_at__lte={tomorrow.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == message.pk

    def test_search_preset_message(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        create_preset_message(user=user, title="Searchable Title", content="Unique content")
        create_preset_message(user=user, title="Another Title", content="Different content")

        # 제목으로 검색
        url = reverse("preset_message:preset-message-list-create") + "?search=Searchable"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Searchable Title"

        # 내용으로 검색
        url = reverse("preset_message:preset-message-list-create") + "?search=Unique"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "Unique content"

    def test_sort_preset_message(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        create_preset_message(user=user, title="B Title")
        create_preset_message(user=user, title="A Title")

        # 제목순 정렬
        url = reverse("preset_message:preset-message-list-create") + "?ordering=title"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["title"] == "A Title"
        assert response.data["results"][1]["title"] == "B Title"

    def test_get_preset_message_detail(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        message = create_preset_message(user=user)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == message.title

    def test_update_preset_message(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        message = create_preset_message(user=user)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        updated_data = {"title": "Updated Title", "is_active": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.title == "Updated Title"
        assert not message.is_active

    def test_delete_preset_message(self, api_client, authenticate_client, create_preset_message):
        user = authenticate_client()
        message = create_preset_message(user=user)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PresetMessage.objects.filter(pk=message.pk).exists()

    def test_user_cannot_update_other_users_preset_message(
        self, api_client, authenticate_client, create_preset_message, create_user
    ):
        user1 = authenticate_client()
        user2 = create_user("another_user@example.com", "pass123")
        message = create_preset_message(user=user2)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        updated_data = {"title": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_any_preset_message(
        self, api_client, authenticate_client, create_preset_message, create_user
    ):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_user2@example.com", "pass123")
        message = create_preset_message(user=user2)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        updated_data = {"title": "Admin Updated Title"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.title == "Admin Updated Title"

    def test_user_cannot_delete_other_users_preset_message(
        self, api_client, authenticate_client, create_preset_message, create_user
    ):
        user1 = authenticate_client()
        user2 = create_user("another_user3@example.com", "pass123")
        message = create_preset_message(user=user2)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any_preset_message(
        self, api_client, authenticate_client, create_preset_message, create_user
    ):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_user4@example.com", "pass123")
        message = create_preset_message(user=user2)
        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PresetMessage.objects.filter(pk=message.pk).exists()

    def test_unauthorized_access(self, api_client, create_preset_message, create_user):
        user = create_user("user5@example.com", "pass123")
        message = create_preset_message(user=user)

        # 인증되지 않은 상태에서 API 접근 시도
        url = reverse("preset_message:preset-message-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        url = reverse("preset_message:preset-message-detail", kwargs={"pk": message.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
