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
def create_notice(db, create_user):
    def _create_notice(author=None, **kwargs):
        if author is None:
            author = create_user("default_notice_author@example.com", "testpass123!")
        return Notice.objects.create(
            title=f"Notice Title {timezone.now().timestamp()}",
            content=f"Notice Content {timezone.now().timestamp()}",
            author=author,
            **kwargs,
        )

    return _create_notice


@pytest.mark.django_db
class TestNoticeAPI:
    def test_create_notice(self, api_client, authenticate_client):
        user = authenticate_client()
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
        assert response.data["title"] == "Test Notice"
        assert response.data["author"]["id"] == user.pk

    def test_get_notice_list(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        create_notice(author=user, title="Notice 1")
        create_notice(author=user, title="Notice 2")
        create_notice(author=user, title="Notice 3", is_published=False)

        url = reverse("notice:notice-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_filter_notice_by_published_status(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        create_notice(author=user, title="Published Notice", is_published=True)
        create_notice(author=user, title="Unpublished Notice", is_published=False)

        url = reverse("notice:notice-list-create") + "?is_published=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Published Notice"

    def test_filter_notice_by_important_status(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        create_notice(author=user, title="Important Notice", is_important=True)
        create_notice(author=user, title="Regular Notice", is_important=False)

        url = reverse("notice:notice-list-create") + "?is_important=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Important Notice"

    def test_filter_notice_by_date_range(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        notice = create_notice(author=user, title="Date Range Test", created_at=today)

        url = (
            reverse("notice:notice-list-create")
            + f"?created_at__gte={yesterday.date()}&created_at__lte={tomorrow.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == notice.pk

    def test_search_notice(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        create_notice(author=user, title="Searchable Title", content="Unique content")
        create_notice(author=user, title="Another Title", content="Different content")

        # 제목으로 검색
        url = reverse("notice:notice-list-create") + "?search=Searchable"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Searchable Title"

        # 내용으로 검색
        url = reverse("notice:notice-list-create") + "?search=Unique"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "Unique content"

    def test_sort_notice(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        create_notice(author=user, title="Notice 1", view_count=10)
        create_notice(author=user, title="Notice 2", view_count=20)

        # 조회수순 정렬
        url = reverse("notice:notice-list-create") + "?ordering=-view_count"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["view_count"] == 20
        assert response.data["results"][1]["view_count"] == 10

    def test_get_notice_detail(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == notice.title
        assert response.data["view_count"] == 1  # 조회수 증가 확인

    def test_update_notice(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        updated_data = {"title": "Updated Title", "is_published": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        notice.refresh_from_db()
        assert notice.title == "Updated Title"
        assert not notice.is_published

    def test_delete_notice(self, api_client, authenticate_client, create_notice):
        user = authenticate_client()
        notice = create_notice(author=user)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notice.objects.filter(pk=notice.pk).exists()

    def test_user_cannot_update_other_users_notice(self, api_client, authenticate_client, create_notice, create_user):
        user1 = authenticate_client()
        user2 = create_user("another_user@example.com", "pass123")
        notice = create_notice(author=user2)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        updated_data = {"title": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_delete_other_users_notice(self, api_client, authenticate_client, create_notice, create_user):
        user1 = authenticate_client()
        user2 = create_user("another_user2@example.com", "pass123")
        notice = create_notice(author=user2)
        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_recent_notice_list(self, api_client, create_notice, create_user):
        user = create_user("notice_author@example.com", "pass123")
        create_notice(author=user, title="Recent Notice 1", is_published=True)
        create_notice(author=user, title="Recent Notice 2", is_published=True)
        create_notice(author=user, title="Recent Notice 3", is_published=True)
        create_notice(author=user, title="Recent Notice 4", is_published=True)
        create_notice(author=user, title="Recent Notice 5", is_published=True)
        create_notice(author=user, title="Recent Notice 6", is_published=True)

        url = reverse("notice:recent-notice-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 5  # 최근 5개만 반환

    def test_unauthorized_access(self, api_client, create_notice, create_user):
        user = create_user("user3@example.com", "pass123")
        notice = create_notice(author=user)

        # 인증되지 않은 상태에서 API 접근 시도
        url = reverse("notice:notice-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK  # 조회는 가능

        url = reverse("notice:notice-detail", kwargs={"pk": notice.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK  # 조회는 가능

        # 수정/삭제는 불가능
        response = api_client.patch(url, {"title": "Unauthorized Update"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
