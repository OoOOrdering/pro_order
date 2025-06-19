from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.notice.models import Notice
from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate_client(api_client):
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
def create_notice(db, create_user):
    def _create_notice(author=None, **kwargs):
        if author is None:
            author = create_user("default_notice_author@example.com", "testpass123!")
        default_title = f"Notice Title {timezone.now().timestamp()}"
        default_content = f"Notice Content {timezone.now().timestamp()}"

        notice_data = {"title": default_title, "content": default_content, **kwargs}
        return Notice.objects.create(author=author, **notice_data)

    return _create_notice


@pytest.mark.django_db
class TestNoticeAPI:
    def test_create_notice(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        url = reverse("notice:notice-list-create")
        data = {
            "title": "Test Notice",
            "content": "This is a test notice.",
            "is_published": True,
            "is_important": False,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Notice.objects.count() == 1
        assert response.data["data"]["title"] == "Test Notice"
        assert response.data["data"]["author"]["id"] == user.pk

    def test_get_notice_list(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Notice 1")
        create_notice(author=user, title="Notice 2")
        create_notice(author=user, title="Notice 3", is_published=False)
        url = reverse("notice:notice-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_filter_notice_by_published_status(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Published Notice", is_published=True)
        create_notice(author=user, title="Unpublished Notice", is_published=False)
        url = reverse("notice:notice-list-create") + "?is_published=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Published Notice"

    def test_filter_notice_by_important_status(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Important Notice", is_important=True)
        create_notice(author=user, title="Regular Notice", is_important=False)
        url = reverse("notice:notice-list-create") + "?is_important=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Important Notice"

    def test_filter_notice_by_date_range(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        notice = create_notice(author=user, title="Date Range Test")
        notice.created_at = today
        notice.save(update_fields=["created_at"])
        url = (
            reverse("notice:notice-list-create")
            + f"?created_at__gte={yesterday.date()}&created_at__lte={tomorrow.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == notice.pk

    def test_search_notice(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Searchable Title", content="Unique content")
        create_notice(author=user, title="Another Title", content="Different content")
        url = reverse("notice:notice-list-create") + "?search=Searchable"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Searchable Title"
        url = reverse("notice:notice-list-create") + "?search=Unique"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "Unique content"

    def test_sort_notice(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Notice 1", view_count=10)
        create_notice(author=user, title="Notice 2", view_count=20)
        url = reverse("notice:notice-list-create") + "?ordering=-view_count"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["view_count"] == 20
        assert response.data["results"][1]["view_count"] == 10

    def test_get_notice_detail(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == notice.title
        assert response.data["view_count"] == 1

    def test_update_notice(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        updated_data = {"title": "Updated Title", "is_published": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        notice.refresh_from_db()
        assert notice.title == "Updated Title"
        assert not notice.is_published

    def test_delete_notice(self, api_client, create_user, create_notice):
        user = create_user()
        api_client.force_authenticate(user=user)
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notice.objects.filter(pk=notice.pk).exists()

    def test_user_cannot_update_other_users_notice(self, api_client, create_user, create_notice):
        import uuid

        user1 = create_user(nickname=f"user1_{uuid.uuid4().hex[:8]}")
        user2 = create_user(nickname=f"user2_{uuid.uuid4().hex[:8]}")
        api_client.force_authenticate(user=user1)
        notice = create_notice(author=user2)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        updated_data = {"title": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_delete_other_users_notice(self, api_client, create_user, create_notice):
        import uuid

        user1 = create_user(nickname=f"user1_{uuid.uuid4().hex[:8]}")
        user2 = create_user(nickname=f"user2_{uuid.uuid4().hex[:8]}")
        api_client.force_authenticate(user=user1)
        notice = create_notice(author=user2)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_recent_notice_list(self, api_client, create_notice, create_user):
        user = create_user("notice_author@example.com", "pass123")
        api_client.force_authenticate(user=user)
        create_notice(author=user, title="Recent Notice 1", is_published=True)
        create_notice(author=user, title="Recent Notice 2", is_published=True)
        create_notice(author=user, title="Recent Notice 3", is_published=True)
        create_notice(author=user, title="Recent Notice 4", is_published=True)
        create_notice(author=user, title="Recent Notice 5", is_published=True)
        create_notice(author=user, title="Recent Notice 6", is_published=True)
        url = reverse("notice:recent-notice-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_unauthorized_access(self, api_client, create_notice, create_user):
        user = create_user("user3@example.com", "pass123")
        notice = create_notice(author=user)
        url = reverse("notice:notice-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response = api_client.patch(url, {"title": "Unauthorized Update"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
