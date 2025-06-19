from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cs_post.models import CSPost
from apps.cs_reply.models import CSReply
from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate_client(api_client):
    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            now = timezone.now()
            nickname = f"test_user_{now.timestamp()}"
            user = User.objects.create_user(
                email=f"test_user_{now.timestamp()}@example.com",
                password="testpass123!",
                is_staff=is_staff,
                nickname=nickname,
            )
        response = api_client.post(reverse("user:token_login"), {"email": user.email, "password": "testpass123!"})
        assert response.status_code == status.HTTP_200_OK, f"Login failed: {response.data}"
        assert "message" in response.data
        assert "data" in response.data
        access_token = response.data["data"]["access_token"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        return user

    return _authenticate_client


@pytest.fixture
def create_cs_post():
    def _create_cs_post(author, **kwargs):
        return CSPost.objects.create(
            author=author,
            post_type=kwargs.get("post_type", CSPost.POST_TYPE_CHOICES[0][0]),
            title=kwargs.get("title", f"Test Inquiry {timezone.now().timestamp()}"),
            content=kwargs.get("content", "This is a test inquiry content."),
            status=kwargs.get("status", CSPost.STATUS_CHOICES[0][0]),
            **{k: v for k, v in kwargs.items() if k not in ["post_type", "title", "content", "status"]},
        )

    return _create_cs_post


@pytest.fixture
def create_cs_reply():
    def _create_cs_reply(cs_post, author, **kwargs):
        return CSReply.objects.create(
            post=cs_post,
            author=author,
            content=kwargs.get("content", f"Reply content {timezone.now().timestamp()}"),
            **{k: v for k, v in kwargs.items() if k != "content"},
        )

    return _create_cs_reply


@pytest.mark.django_db
class TestCSReplyAPI:
    def test_create_cs_reply_by_admin(self, api_client, create_user):
        admin = create_user(is_staff=True)
        api_client.force_authenticate(user=admin)

        # 일반 사용자가 작성한 게시물 생성
        now = timezone.now()
        normal_user = User.objects.create_user(
            email=f"normal_user_{now.timestamp()}@example.com",
            password="testpass123!",
            nickname=f"normal_user_{now.timestamp()}",
        )
        cs_post = CSPost.objects.create(
            author=normal_user,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {now.timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        data = {
            "content": "This is an admin's test reply.",
        }

        response = api_client.post(url, data, format="json")
        print("RESPONSE DATA:", response.data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "message" in response.data
        assert "data" in response.data
        assert response.data["data"]["content"] == data["content"]
        assert response.data["data"]["author"]["id"] == admin.id
        assert response.data["data"]["post"]["id"] == cs_post.id

    def test_create_cs_reply_by_non_admin(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        cs_post = CSPost.objects.create(
            author=user,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        data = {
            "content": "This is a normal user's test reply.",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data, "Response data is missing 'detail' key"
        assert response.data["detail"] == "관리자만 답변을 작성할 수 있습니다."

    def test_list_cs_replies(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        # CS 게시물과 답변들 생성
        cs_post = CSPost.objects.create(
            author=user,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )
        for i in range(3):  # 여러 개의 답변 생성
            CSReply.objects.create(post=cs_post, author=user, content=f"Reply content {i+1}")

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert "data" in response.data
        if "results" in response.data["data"]:  # 페이지네이션이 적용된 경우
            assert "count" in response.data["data"]
            assert len(response.data["data"]["results"]) == 3
        else:  # 페이지네이션이 적용되지 않은 경우
            assert len(response.data["data"]) == 3

    def test_retrieve_cs_reply(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        cs_post = CSPost.objects.create(
            author=user,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )
        cs_reply = CSReply.objects.create(post=cs_post, author=user, content="This is a test reply content.")

        url = reverse("cs_reply:cs-reply-detail", kwargs={"cs_post_pk": cs_post.pk, "pk": cs_reply.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert "data" in response.data
        assert response.data["data"]["id"] == cs_reply.id
        assert response.data["data"]["content"] == cs_reply.content

    def test_update_cs_reply_by_admin(self, api_client, create_user):
        admin = create_user(is_staff=True)
        api_client.force_authenticate(user=admin)

        cs_post = CSPost.objects.create(
            author=admin,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )
        cs_reply = CSReply.objects.create(post=cs_post, author=admin, content="This is a test reply content.")

        url = reverse("cs_reply:cs-reply-detail", kwargs={"cs_post_pk": cs_post.pk, "pk": cs_reply.pk})
        update_data = {"content": "Updated reply content"}
        response = api_client.put(url, update_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert "data" in response.data
        assert response.data["data"]["content"] == update_data["content"]
        assert response.data["data"]["author"]["id"] == admin.id

    def test_update_cs_reply_by_non_admin(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        # 답변 수정 시도
        url = reverse("cs_reply:cs-reply-detail", kwargs={"cs_post_pk": 1, "pk": 1})
        update_data = {"content": "Attempt to update by normal user"}
        response = api_client.put(url, update_data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
        assert response.data["detail"] == "관리자만 답변을 수정할 수 있습니다."

    def test_delete_cs_reply_by_admin(self, api_client, create_user):
        admin = create_user(is_staff=True)
        api_client.force_authenticate(user=admin)

        cs_post = CSPost.objects.create(
            author=admin,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )
        cs_reply = CSReply.objects.create(post=cs_post, author=admin, content="This is a test reply content.")

        url = reverse("cs_reply:cs-reply-detail", kwargs={"cs_post_pk": cs_post.pk, "pk": cs_reply.pk})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CSReply.objects.filter(pk=cs_reply.pk).exists()

    def test_delete_cs_reply_by_non_admin(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        url = reverse("cs_reply:cs-reply-detail", kwargs={"cs_post_pk": 1, "pk": 1})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
        assert response.data["detail"] == "관리자만 답변을 삭제할 수 있습니다."

    def test_list_cs_replies_with_pagination(self, api_client, create_user):
        user = create_user()
        api_client.force_authenticate(user=user)

        cs_post = CSPost.objects.create(
            author=user,
            post_type=CSPost.POST_TYPE_CHOICES[0][0],
            title=f"Test Inquiry {timezone.now().timestamp()}",
            content="This is a test inquiry content.",
            status=CSPost.STATUS_CHOICES[0][0],
        )
        # 페이지네이션 테스트를 위해 여러 개의 답변 생성
        for i in range(15):
            CSReply.objects.create(post=cs_post, author=user, content=f"Reply content {i+1}")

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "message" in response.data
        assert "data" in response.data
        assert "count" in response.data["data"]
        assert "results" in response.data["data"]
        assert response.data["data"]["count"] == 15  # 전체 답변 수
        assert len(response.data["data"]["results"]) <= 10  # 기본 페이지 크기
