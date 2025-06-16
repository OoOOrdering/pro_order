from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.like.models import Like
from apps.order.models import Order  # 좋아요 대상 모델 (예시)
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
def create_order(db, create_user):
    def _create_order(user, **kwargs):
        return Order.objects.create(
            user=user,
            order_number=f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            status=Order.OrderStatus.PENDING,
            total_amount="100.00",
            payment_method="Credit Card",
            payment_status="PAID",
            shipping_address="123 Test St",
            shipping_phone="123-456-7890",
            shipping_name="Test Recipient",
            **kwargs,
        )

    return _create_order


@pytest.fixture
def create_like(db, create_user, create_order):
    def _create_like(user, content_object, **kwargs):
        content_type = ContentType.objects.get_for_model(content_object)
        return Like.objects.create(user=user, content_type=content_type, object_id=content_object.pk, **kwargs)

    return _create_like


@pytest.mark.django_db
class TestLikeAPI:
    def test_create_like_on_order(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        order_content_type = ContentType.objects.get_for_model(Order)
        url = reverse("like:like-list-create")
        data = {"content_type": order_content_type.pk, "object_id": order.pk}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Like.objects.count() == 1
        assert response.data["object_id"] == order.pk
        assert response.data["content_type_name"] == "order"

    def test_cannot_like_same_item_twice(self, api_client, authenticate_client, create_order, create_like):
        user = authenticate_client()
        order = create_order(user=user)
        create_like(user=user, content_object=order)

        order_content_type = ContentType.objects.get_for_model(Order)
        url = reverse("like:like-list-create")
        data = {"content_type": order_content_type.pk, "object_id": order.pk}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "You have already liked this item." in str(response.data)

    def test_get_user_likes_list(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=user)
        create_like(user=user, content_object=order1)
        create_like(user=user, content_object=order2)
        url = reverse("like:like-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_likes_by_content_type(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=user)  # 다른 유형의 객체 추가를 위해 일단 Order로

        order_content_type = ContentType.objects.get_for_model(Order)
        # 다른 모델이 있다면 추가할 수 있음
        # from apps.post.models import Post
        # post = create_post(user=user)
        # post_content_type = ContentType.objects.get_for_model(Post)

        like_order1 = create_like(user=user, content_object=order1)
        # like_post = create_like(user=user, content_object=post)

        url = reverse("like:like-list-create") + f"?content_type={order_content_type.pk}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == like_order1.pk
        assert response.data["results"][0]["content_type_name"] == "order"

    def test_filter_likes_by_object_id(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=user)

        like1 = create_like(user=user, content_object=order1)
        like2 = create_like(user=user, content_object=order2)

        url = reverse("like:like-list-create") + f"?object_id={order1.pk}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == like1.pk

    def test_filter_likes_by_created_at(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=user)

        old_like = create_like(
            user=user,
            content_object=order1,
            created_at=timezone.now() - timedelta(days=2),
        )
        new_like = create_like(
            user=user,
            content_object=order2,
            created_at=timezone.now() - timedelta(days=1),
        )

        url = (
            reverse("like:like-list-create")
            + f"?created_at__gte={(timezone.now() - timedelta(days=3)).date()}&created_at__lte={(timezone.now()).date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        url = (
            reverse("like:like-list-create")
            + f"?created_at__gte={(timezone.now() - timedelta(days=1, seconds=1)).date()}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == new_like.pk

    def test_sort_likes_by_created_at(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=user)
        order3 = create_order(user=user)

        like1 = create_like(
            user=user,
            content_object=order1,
            created_at=timezone.now() - timedelta(days=2),
        )
        like2 = create_like(
            user=user,
            content_object=order2,
            created_at=timezone.now() - timedelta(days=1),
        )
        like3 = create_like(user=user, content_object=order3, created_at=timezone.now())

        # 생성일시 오름차순
        url = reverse("like:like-list-create") + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == like1.pk
        assert response.data["results"][1]["id"] == like2.pk
        assert response.data["results"][2]["id"] == like3.pk

        # 생성일시 내림차순
        url = reverse("like:like-list-create") + "?ordering=-created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == like3.pk
        assert response.data["results"][1]["id"] == like2.pk
        assert response.data["results"][2]["id"] == like1.pk

    def test_destroy_like(self, api_client, authenticate_client, create_like, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        like = create_like(user=user, content_object=order)
        url = reverse("like:like-destroy", kwargs={"pk": like.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Like.objects.filter(pk=like.pk).exists()

    def test_user_cannot_destroy_other_users_like(
        self, api_client, authenticate_client, create_like, create_order, create_user
    ):
        user1 = authenticate_client()
        user2 = create_user("another_liker@example.com", "testpass123!")
        order = create_order(user=user1)  # order is created by user1, but liked by user2
        like = create_like(user=user2, content_object=order)

        # user1이 user2가 누른 좋아요를 삭제 시도
        url = reverse("like:like-destroy", kwargs={"pk": like.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Like.objects.filter(pk=like.pk).exists()  # 좋아요가 삭제되지 않았는지 확인
