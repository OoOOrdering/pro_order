from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.order.models import Order
from apps.review.models import Review
from apps.user.models import User


@pytest.fixture
def create_order(user_factory):
    def _create_order(user, **kwargs):
        order_number = kwargs.pop("order_number", f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}")
        return Order.objects.create(
            user=user,
            order_number=order_number,
            status=kwargs.pop("status", Order.OrderStatus.COMPLETED),
            total_amount=kwargs.pop("total_amount", Decimal("100.00")),
            payment_method=kwargs.pop("payment_method", "Credit Card"),
            payment_status=kwargs.pop("payment_status", "PAID"),
            shipping_address=kwargs.pop("shipping_address", "123 Test St"),
            shipping_phone=kwargs.pop("shipping_phone", "123-456-7890"),
            shipping_name=kwargs.pop("shipping_name", "Test Recipient"),
            **kwargs,
        )

    return _create_order


@pytest.fixture
def create_review():
    def _create_review(order, reviewer=None, **kwargs):
        if reviewer is None:
            reviewer = order.user
        return Review.objects.create(
            order=order,
            reviewer=reviewer,
            rating=kwargs.pop("rating", 5),
            comment=kwargs.pop("comment", "Excellent service!"),
            is_public=kwargs.pop("is_public", True),
            **kwargs,
        )

    return _create_review


@pytest.mark.django_db
class TestReviewAPI:
    @pytest.fixture(autouse=True)
    def setup(self, authenticated_client):
        self.client, self.user = authenticated_client()
        self.list_url = reverse("review:review-list-create")

    def test_create_review(self, create_order):
        order = create_order(user=self.user, status=Order.OrderStatus.COMPLETED)
        data = {"order": order.id, "rating": 4, "comment": "매우 좋은 서비스입니다.", "is_public": True}
        response = self.client.post(self.list_url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["rating"] == 4
        assert response.data["data"]["comment"] == "매우 좋은 서비스입니다."
        assert response.data["data"]["reviewer"] == self.user.id
        assert response.data["data"]["is_public"] == True

    def test_create_review_for_incomplete_order_fails(self, create_order):
        order = create_order(user=self.user, status=Order.OrderStatus.PENDING)
        data = {"order": order.id, "rating": 4, "comment": "매우 좋은 서비스입니다.", "is_public": True}
        response = self.client.post(self.list_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_review_for_others_order_fails(self, create_order, create_user):
        other_user = create_user(is_staff=False)
        order = create_order(user=other_user, status=Order.OrderStatus.COMPLETED)
        data = {"order": order.id, "rating": 4, "comment": "다른 사람의 주문에 리뷰를 작성합니다.", "is_public": True}
        response = self.client.post(self.list_url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_review_list(self, create_order, create_review):
        order = create_order(user=self.user)
        review = create_review(order=order)

        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "count" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) >= 1
        first_review = data["results"][0]
        assert all(k in first_review for k in ("id", "order", "reviewer", "rating", "comment", "is_public"))

    def test_get_review_detail(self, create_order, create_review):
        order = create_order(user=self.user)
        review = create_review(order=order)

        detail_url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == review.pk
        assert response.data["rating"] == review.rating
        assert response.data["comment"] == review.comment
        assert response.data["order"] == order.pk
        assert response.data["reviewer"] == self.user.id

    def test_update_own_review(self, create_order, create_review):
        order = create_order(user=self.user)
        review = create_review(order=order)

        detail_url = reverse("review:review-detail", kwargs={"pk": review.pk})
        update_data = {"rating": 3, "comment": "Updated review comment"}
        response = self.client.patch(detail_url, update_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["rating"] == 3
        assert response.data["comment"] == "Updated review comment"

    def test_delete_own_review(self, create_order, create_review):
        order = create_order(user=self.user)
        review = create_review(order=order)

        detail_url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = self.client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Review.objects.filter(pk=review.pk).exists()
