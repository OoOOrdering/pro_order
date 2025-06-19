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
def authenticate_client(api_client):
    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            timestamp = timezone.now().timestamp()
            user = create_user(
                email=f"test_user_{timestamp}@example.com",
                password="testpass123!",
                nickname=f"test_user_{timestamp}",
                is_staff=is_staff,
            )
        login_url = reverse("user:token_login")
        response = api_client.post(login_url, {"email": user.email, "password": "testpass123!"})
        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            # throttle 제한에 걸린 경우: 강제로 인증
            api_client.force_authenticate(user=user)
        else:
            access_token = response.data.get("data", {}).get("access_token")
            if access_token:
                api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
            else:
                api_client.force_authenticate(user=user)
        return user

    return _authenticate_client


@pytest.fixture
def create_cs_post(create_user):
    def _create_cs_post(author, **kwargs):
        defaults = {
            "post_type": CSPost.POST_TYPE_CHOICES[0][0],
            "title": f"Test Inquiry {timezone.now().timestamp()}",
            "content": "This is a test inquiry content.",
            "status": CSPost.STATUS_CHOICES[0][0],
        }
        # kwargs로 전달된 값으로 defaults를 업데이트
        defaults.update(kwargs)
        # author는 create 호출 시 직접 전달
        return CSPost.objects.create(author=author, **defaults)

    return _create_cs_post


@pytest.mark.django_db
class TestCSPostAPI:
    def test_create_cs_post(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)
        url = reverse("cs_post:cspost-list-create")
        data = {
            "post_type": "report",
            "title": "Bug Report",
            "content": "Found a bug in the system.",
            "attachment_url": "http://example.com/bug.png",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["title"] == "Bug Report"
        assert response.data["data"]["author"]["id"] == user.id
        assert CSPost.objects.count() == 1

    def test_list_cs_posts(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)
        # 게시글 생성
        url = reverse("cs_post:cspost-list-create")
        data = {
            "post_type": "report",
            "title": "Bug Report",
            "content": "Found a bug in the system.",
            "attachment_url": "http://example.com/bug.png",
        }
        api_client.post(url, data, format="json")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 일반 사용자는 본인이 작성한 게시물만 볼 수 있음
        assert response.data["data"]["count"] == 1  # pagination 적용
        assert response.data["data"]["results"][0]["author"]["id"] == user.id

    def test_list_cs_posts_admin(self, api_client, create_user):
        admin = create_user(is_staff=True)
        api_client.force_authenticate(user=admin)
        # 게시글 2개 생성
        url = reverse("cs_post:cspost-list-create")
        data1 = {
            "post_type": "report",
            "title": "Bug Report 1",
            "content": "Found a bug in the system.",
            "attachment_url": "http://example.com/bug1.png",
        }
        data2 = {
            "post_type": "report",
            "title": "Bug Report 2",
            "content": "Found another bug.",
            "attachment_url": "http://example.com/bug2.png",
        }
        api_client.post(url, data1, format="json")
        api_client.post(url, data2, format="json")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # 관리자는 모든 게시물을 볼 수 있음
        assert response.data["data"]["count"] == 2  # pagination 적용

    def test_get_cs_post_detail(self, api_client, create_user, create_cs_post):
        user = create_user()
        cs_post = create_cs_post(author=user)
        api_client.force_authenticate(user=user)
        url = reverse("cs_post:cspost-detail", args=[cs_post.id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["id"] == cs_post.id
        assert response.data["data"]["title"] == cs_post.title

    def test_get_other_user_cs_post_detail(self, api_client, create_user, create_cs_post):
        user1 = create_user()
        user2 = create_user()
        cs_post = create_cs_post(author=user2)
        api_client.force_authenticate(user=user1)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": cs_post.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_cs_post(self, api_client, create_user, create_cs_post):
        user = create_user()
        cs_post = create_cs_post(author=user)
        api_client.force_authenticate(user=user)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": cs_post.pk})
        update_data = {"title": "Updated Title", "content": "Updated content"}
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["title"] == "Updated Title"
        assert response.data["data"]["content"] == "Updated content"

    def test_update_other_user_cs_post(self, api_client, create_user, create_cs_post):
        user1 = create_user()
        user2 = create_user()
        cs_post = create_cs_post(author=user2)
        api_client.force_authenticate(user=user1)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": cs_post.pk})
        update_data = {"title": "Should not update"}
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_cs_post(self, api_client, create_user, create_cs_post):
        user = create_user()
        cs_post = create_cs_post(author=user)
        api_client.force_authenticate(user=user)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": cs_post.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CSPost.objects.filter(id=cs_post.id).exists()

    def test_admin_manage_cs_post(self, api_client, create_user, create_cs_post):
        """관리자가 모든 CS 게시물을 관리할 수 있는지 테스트"""
        admin = create_user(is_staff=True)
        cs_post = create_cs_post(author=admin, title="Test Admin Post", status="pending")
        api_client.force_authenticate(user=admin)
        url = reverse("cs_post:cspost-detail", kwargs={"pk": cs_post.pk})
        update_data = {"status": "completed"}
        response = api_client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == "completed"
