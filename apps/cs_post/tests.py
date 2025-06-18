from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cs_post.models import CSPost
from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user():
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
def create_cs_post(create_user):
    def _create_cs_post(author, **kwargs):
        return CSPost.objects.create(
            author=author,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
            **kwargs,
        )

    return _create_cs_post


@pytest.mark.django_db
class TestCSPostAPI:
    def test_create_cs_post(self, api_client, authenticate_client):
        user = authenticate_client()
        url = reverse("cs_post:cspost-list-create")
        data = {
            "post_type": "report",
            "title": "Bug Report",
            "content": "Found a bug in the system.",
            "attachment_url": "http://example.com/bug.png",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert CSPost.objects.count() == 1
        assert response.data["title"] == "Bug Report"
        assert response.data["author"]["id"] == user.pk

    def test_get_cs_post_list(self, api_client, authenticate_client, create_cs_post):
        user1 = authenticate_client()
        user2 = create_user("reporter2@example.com", "testpass123!")
        create_cs_post(author=user1, title="User1 Inquiry")
        create_cs_post(author=user2, title="User2 Report", post_type="report")

        url = reverse("cs_post:cspost-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 일반 사용자는 본인이 작성한 게시물만 볼 수 있음
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["author"]["id"] == user1.pk

    def test_get_cs_post_list_admin(self, api_client, authenticate_client, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        user1 = create_user("reporter3@example.com", "testpass123!")
        create_cs_post(author=user1, title="User3 Inquiry")
        create_cs_post(author=admin_user, title="Admin Inquiry")

        url = reverse("cs_post:cspost-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 관리자는 모든 게시물을 볼 수 있음
        assert len(response.data["results"]) == 2

    def test_filter_cs_post_by_type_and_status(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        create_cs_post(author=user, post_type="inquiry", status="pending")
        create_cs_post(author=user, post_type="report", status="completed")
        url = reverse("cs_post:cspost-list-create") + "?post_type=inquiry&status=pending"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["post_type"] == "inquiry"
        assert response.data["results"][0]["status"] == "pending"

    def test_filter_cs_post_by_created_at_range(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        post1 = create_cs_post(author=user, title="Old Post", created_at=two_days_ago)
        post2 = create_cs_post(author=user, title="New Post", created_at=yesterday)

        url = (
            reverse("cs_post:cspost-list-create")
            + f"?created_at__gte={two_days_ago.date()}&created_at__lte={today.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        url = reverse("cs_post:cspost-list-create") + f"?created_at__gte={yesterday.date()}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == post2.pk

    def test_filter_cs_post_by_status(
        self,
        api_client,
        authenticate_client,
        create_cs_post,
    ):
        user = authenticate_client()
        create_cs_post(author=user, post_type="inquiry", status="pending")
        create_cs_post(author=user, post_type="report", status="completed")
        url = reverse("cs_post:cspost-list-create") + "?post_type=inquiry&status=pending"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["post_type"] == "inquiry"
        assert response.data["results"][0]["status"] == "pending"

    def test_search_cs_post_by_title_content_or_author_email(
        self,
        api_client,
        authenticate_client,
        create_cs_post,
    ):
        user = authenticate_client()
        user_email = user.email
        create_cs_post(
            author=user,
            title="Searchable Title Here",
            content="This is content with a keyword.",
        )
        create_cs_post(author=user, title="Another Post", content="Irrelevant content.")

        # 제목으로 검색
        url = reverse("cs_post:cspost-list-create") + "?search=Searchable"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Searchable Title Here"

        # 내용으로 검색
        url = reverse("cs_post:cspost-list-create") + "?search=keyword"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "This is content with a keyword."

        # 작성자 이메일로 검색 (관리자 권한 필요)
        admin_user = authenticate_client(is_staff=True)
        create_cs_post(author=user, title="Post by specific user")
        url = reverse("cs_post:cspost-list-create") + f"?search={user_email}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1  # 해당 유저의 모든 게시물이 검색됨

    def test_sort_cs_post_by_created_at(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        post1 = create_cs_post(author=user, created_at=timezone.now() - timedelta(days=2), title="Post C")
        post2 = create_cs_post(author=user, created_at=timezone.now() - timedelta(days=1), title="Post B")
        post3 = create_cs_post(author=user, created_at=timezone.now(), title="Post A")

        # 생성일시 오름차순
        url = reverse("cs_post:cspost-list-create") + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == post1.pk
        assert response.data["results"][1]["id"] == post2.pk
        assert response.data["results"][2]["id"] == post3.pk

        # 생성일시 내림차순
        url = reverse("cs_post:cspost-list-create") + "?ordering=-created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == post3.pk
        assert response.data["results"][1]["id"] == post2.pk
        assert response.data["results"][2]["id"] == post1.pk

    def test_sort_cs_post_by_title(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        post1 = create_cs_post(author=user, title="Zulu")
        post2 = create_cs_post(author=user, title="Alpha")
        post3 = create_cs_post(author=user, title="Charlie")

        # 제목 오름차순
        url = reverse("cs_post:cspost-list-create") + "?ordering=title"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == post2.pk  # Alpha
        assert response.data["results"][1]["id"] == post3.pk  # Charlie
        assert response.data["results"][2]["id"] == post1.pk  # Zulu

    def test_get_cs_post_detail(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        post = create_cs_post(author=user)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == post.pk
        assert response.data["title"] == post.title

    def test_update_cs_post(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        post = create_cs_post(author=user)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        updated_data = {"title": "Updated Title", "status": "in_progress"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == "Updated Title"
        assert post.status == "in_progress"

    def test_delete_cs_post(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client()
        post = create_cs_post(author=user)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CSPost.objects.filter(pk=post.pk).exists()

    def test_user_cannot_update_other_users_cs_post(self, api_client, authenticate_client, create_cs_post, create_user):
        user1 = authenticate_client()
        user2 = create_user("another_author@example.com", "testpass123!")
        post = create_cs_post(author=user2)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        updated_data = {"title": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_any_cs_post(self, api_client, authenticate_client, create_cs_post, create_user):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_author_admin@example.com", "testpass123!")
        post = create_cs_post(author=user2)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        updated_data = {"title": "Admin Updated Title"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == "Admin Updated Title"

    def test_user_cannot_delete_other_users_cs_post(self, api_client, authenticate_client, create_cs_post, create_user):
        user1 = authenticate_client()
        user2 = create_user("another_author_delete@example.com", "testpass123!")
        post = create_cs_post(author=user2)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any_cs_post(self, api_client, authenticate_client, create_cs_post, create_user):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_author_delete_admin@example.com", "testpass123!")
        post = create_cs_post(author=user2)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": post.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CSPost.objects.filter(pk=post.pk).exists()
