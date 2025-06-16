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
def create_cs_post(db, create_user):
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


@pytest.fixture
def create_cs_reply(db, create_user, create_cs_post):
    def _create_cs_reply(cs_post, author, **kwargs):
        return CSReply.objects.create(
            post=cs_post,
            author=author,
            content=f"Reply content {timezone.now().timestamp()}",
            **kwargs,
        )

    return _create_cs_reply


@pytest.mark.django_db
class TestCSReplyAPI:
    def test_create_cs_reply(self, api_client, authenticate_client, create_cs_post):
        admin_user = authenticate_client(is_staff=True)  # 관리자만 답변 생성 가능하다고 가정
        cs_post = create_cs_post(author=admin_user)  # 게시물 작성
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        data = {
            "content": "This is a test reply.",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert CSReply.objects.count() == 1
        assert response.data["content"] == "This is a test reply."
        assert response.data["author"]["id"] == admin_user.pk

    def test_get_cs_reply_list_by_admin(
        self,
        api_client,
        authenticate_client,
        create_cs_reply,
        create_cs_post,
        create_user,
    ):
        admin_user = authenticate_client(is_staff=True)
        user1 = create_user("user1@example.com", "testpass123!")
        user2 = create_user("user2@example.com", "testpass123!")
        cs_post1 = create_cs_post(author=user1)
        cs_post2 = create_cs_post(author=user2)
        create_cs_reply(cs_post=cs_post1, author=admin_user, content="Reply for post 1")
        create_cs_reply(cs_post=cs_post2, author=admin_user, content="Reply for post 2")

        # 관리자는 모든 답변 조회 가능
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post1.pk})  # cs_post_pk는 여전히 필요
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1  # cs_post1에 대한 답변만 보여야 함
        assert response.data["results"][0]["content"] == "Reply for post 1"

    def test_get_cs_reply_list_by_normal_user_sees_own_post_replies(
        self,
        api_client,
        authenticate_client,
        create_cs_reply,
        create_cs_post,
        create_user,
    ):
        normal_user = authenticate_client()
        other_user = create_user("otheruser@example.com", "testpass123!")
        staff_user = create_user("staff@example.com", "testpass123!", is_staff=True)

        cs_post_for_user = create_cs_post(author=normal_user)
        cs_post_for_other = create_cs_post(author=other_user)

        create_cs_reply(cs_post=cs_post_for_user, author=staff_user, content="Reply for user's post")
        create_cs_reply(
            cs_post=cs_post_for_other,
            author=staff_user,
            content="Reply for other's post",
        )

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post_for_user.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "Reply for user's post"

        # 다른 사용자의 게시물에 대한 답변은 조회 불가
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post_for_other.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_filter_cs_reply_by_author(
        self,
        api_client,
        authenticate_client,
        create_cs_reply,
        create_cs_post,
        create_user,
    ):
        admin_user = authenticate_client(is_staff=True)
        user1 = create_user("filter_author1@example.com", "testpass123!")
        user2 = create_user("filter_author2@example.com", "testpass123!")

        cs_post = create_cs_post(author=user1)
        reply1 = create_cs_reply(cs_post=cs_post, author=admin_user, content="Reply by Admin")
        reply2 = create_cs_reply(cs_post=cs_post, author=user1, content="Reply by User1")

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk}) + f"?author={admin_user.pk}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == reply1.pk

    def test_filter_cs_reply_by_created_at_range(
        self, api_client, authenticate_client, create_cs_reply, create_cs_post
    ):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        reply1 = create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            content="Old Reply",
            created_at=two_days_ago,
        )
        reply2 = create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            content="New Reply",
            created_at=yesterday,
        )

        url = (
            reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
            + f"?created_at__gte={two_days_ago.date()}&created_at__lte={today.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        url = (
            reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
            + f"?created_at__gte={yesterday.date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == reply2.pk

    def test_search_cs_reply_by_content(self, api_client, authenticate_client, create_cs_reply, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)
        create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            content="This reply has a specific keyword.",
        )
        create_cs_reply(cs_post=cs_post, author=admin_user, content="Another reply.")

        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk}) + "?search=keyword"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["content"] == "This reply has a specific keyword."

    def test_sort_cs_reply_by_created_at(self, api_client, authenticate_client, create_cs_reply, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)

        reply1 = create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            created_at=timezone.now() - timedelta(days=2),
            content="Reply C",
        )
        reply2 = create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            created_at=timezone.now() - timedelta(days=1),
            content="Reply B",
        )
        reply3 = create_cs_reply(
            cs_post=cs_post,
            author=admin_user,
            created_at=timezone.now(),
            content="Reply A",
        )

        # 생성일시 오름차순
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk}) + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == reply1.pk
        assert response.data["results"][1]["id"] == reply2.pk
        assert response.data["results"][2]["id"] == reply3.pk

        # 생성일시 내림차순
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk}) + "?ordering=-created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == reply3.pk
        assert response.data["results"][1]["id"] == reply2.pk
        assert response.data["results"][2]["id"] == reply1.pk

    def test_get_cs_reply_detail(self, api_client, authenticate_client, create_cs_reply, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)
        reply = create_cs_reply(cs_post=cs_post, author=admin_user)
        url = reverse(
            "cs_reply:cs-reply-detail",
            kwargs={"cs_post_pk": cs_post.pk, "pk": reply.pk},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == reply.pk
        assert response.data["content"] == reply.content

    def test_update_cs_reply(self, api_client, authenticate_client, create_cs_reply, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)
        reply = create_cs_reply(cs_post=cs_post, author=admin_user)
        url = reverse(
            "cs_reply:cs-reply-detail",
            kwargs={"cs_post_pk": cs_post.pk, "pk": reply.pk},
        )
        updated_data = {"content": "Updated reply content"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        reply.refresh_from_db()
        assert reply.content == "Updated reply content"

    def test_delete_cs_reply(self, api_client, authenticate_client, create_cs_reply, create_cs_post):
        admin_user = authenticate_client(is_staff=True)
        cs_post = create_cs_post(author=admin_user)
        reply = create_cs_reply(cs_post=cs_post, author=admin_user)
        url = reverse(
            "cs_reply:cs-reply-detail",
            kwargs={"cs_post_pk": cs_post.pk, "pk": reply.pk},
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CSReply.objects.filter(pk=reply.pk).exists()

    def test_non_admin_cannot_create_cs_reply(self, api_client, authenticate_client, create_cs_post):
        user = authenticate_client(is_staff=False)
        cs_post = create_cs_post(author=user)
        url = reverse("cs_reply:cs-reply-list-create", kwargs={"cs_post_pk": cs_post.pk})
        data = {"content": "Non-admin reply attempt."}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_cannot_update_cs_reply(
        self,
        api_client,
        authenticate_client,
        create_cs_reply,
        create_cs_post,
        create_user,
    ):
        admin_user = create_user("admin_for_reply@example.com", "testpass123!", is_staff=True)
        regular_user = authenticate_client(is_staff=False)
        cs_post = create_cs_post(author=regular_user)
        reply = create_cs_reply(cs_post=cs_post, author=admin_user)
        url = reverse(
            "cs_reply:cs-reply-detail",
            kwargs={"cs_post_pk": cs_post.pk, "pk": reply.pk},
        )
        updated_data = {"content": "Attempted update by non-admin"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_cannot_delete_cs_reply(
        self,
        api_client,
        authenticate_client,
        create_cs_reply,
        create_cs_post,
        create_user,
    ):
        admin_user = create_user("admin_for_delete@example.com", "testpass123!", is_staff=True)
        regular_user = authenticate_client(is_staff=False)
        cs_post = create_cs_post(author=regular_user)
        reply = create_cs_reply(cs_post=cs_post, author=admin_user)
        url = reverse(
            "cs_reply:cs-reply-detail",
            kwargs={"cs_post_pk": cs_post.pk, "pk": reply.pk},
        )
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
