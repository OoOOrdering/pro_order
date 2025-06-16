from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.order.models import Order
from apps.review.models import Review
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
            status=Order.OrderStatus.COMPLETED,  # 리뷰는 완료된 주문에 대해 작성 가정
            total_amount=Decimal("100.00"),
            payment_method="Credit Card",
            payment_status="PAID",
            shipping_address="123 Test St",
            shipping_phone="123-456-7890",
            shipping_name="Test Recipient",
            **kwargs,
        )

    return _create_order


@pytest.fixture
def create_review(db, create_order, create_user):
    def _create_review(order, reviewer, **kwargs):
        return Review.objects.create(order=order, reviewer=reviewer, rating=5, comment="Great service!", **kwargs)

    return _create_review


@pytest.mark.django_db
class TestReviewAPI(APITestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.other_user = User.objects.create_user(username="otheruser", password="testpass123")

        # 테스트용 주문 생성
        self.order = Order.objects.create(order_number="TEST-001", user=self.user)

        # 테스트용 리뷰 생성
        self.review = Review.objects.create(
            order=self.order,
            reviewer=self.user,
            rating=5,
            comment="Great service!",
            is_public=True,
        )

        # API 엔드포인트 URL
        self.list_url = reverse("review-list-create")
        self.detail_url = reverse("review-detail", kwargs={"pk": self.review.pk})

        # 인증
        self.client.force_authenticate(user=self.user)

    def test_create_review(self):
        """리뷰 생성 테스트."""
        data = {
            "order": self.order.id,
            "rating": 4,
            "comment": "Good service",
            "is_public": True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)

    def test_create_duplicate_review(self):
        """중복 리뷰 생성 방지 테스트."""
        data = {
            "order": self.order.id,
            "rating": 4,
            "comment": "Another review",
            "is_public": True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_reviews(self):
        """리뷰 목록 조회 테스트."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filter_reviews_by_rating(self):
        """평점으로 리뷰 필터링 테스트."""
        response = self.client.get(f"{self.list_url}?rating=5")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_search_reviews(self):
        """리뷰 검색 테스트."""
        response = self.client.get(f"{self.list_url}?search=Great")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_sort_reviews(self):
        """리뷰 정렬 테스트."""
        # 새로운 리뷰 생성
        Review.objects.create(
            order=self.order,
            reviewer=self.other_user,
            rating=3,
            comment="Average service",
            is_public=True,
        )

        # 평점 높은순 정렬
        response = self.client.get(f"{self.list_url}?ordering=-rating")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["rating"], 5)

    def test_update_review(self):
        """리뷰 수정 테스트."""
        data = {"rating": 4, "comment": "Updated review", "is_public": True}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.comment, "Updated review")

    def test_delete_review(self):
        """리뷰 삭제 테스트."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)

    def test_unauthorized_access(self):
        """인증되지 않은 접근 테스트."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # 조회는 가능

        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_review_list(self, api_client, authenticate_client, create_review, create_order, create_user):
        user1 = authenticate_client()
        user2 = create_user("reviewer2@example.com", "testpass123!")
        order1 = create_order(user=user1)
        order2 = create_order(user=user2)
        create_review(order=order1, reviewer=user1, rating=5)
        create_review(order=order2, reviewer=user2, rating=4)
        url = reverse("review:review-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_review_by_rating(self, api_client, authenticate_client, create_review, create_order, create_user):
        user = authenticate_client()
        order1 = create_order(user=user)
        order2 = create_order(user=create_user("filter_user@example.com", "pass"))
        create_review(order=order1, reviewer=user, rating=5)
        create_review(order=order2, reviewer=user, rating=3)
        url = reverse("review:review-list-create") + "?rating=5"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["rating"] == 5

    def test_get_review_detail(self, api_client, authenticate_client, create_review, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        review = create_review(order=order, reviewer=user)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == review.pk
        assert response.data["comment"] == review.comment

    def test_update_review(self, api_client, authenticate_client, create_review, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        review = create_review(order=order, reviewer=user)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        updated_data = {"comment": "Updated comment", "rating": 4}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.comment == "Updated comment"
        assert review.rating == 4

    def test_delete_review(self, api_client, authenticate_client, create_review, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        review = create_review(order=order, reviewer=user)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Review.objects.filter(pk=review.pk).exists()

    def test_user_cannot_update_other_users_review(
        self, api_client, authenticate_client, create_review, create_user, create_order
    ):
        user1 = authenticate_client()
        user2 = create_user("another_reviewer@example.com", "pass123")
        order = create_order(user=user2)
        review = create_review(order=order, reviewer=user2)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        updated_data = {"comment": "Attempted update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_update_any_review(
        self, api_client, authenticate_client, create_review, create_user, create_order
    ):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_reviewer_admin@example.com", "pass123")
        order = create_order(user=user2)
        review = create_review(order=order, reviewer=user2)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        updated_data = {"comment": "Admin updated comment"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        review.refresh_from_db()
        assert review.comment == "Admin updated comment"

    def test_user_cannot_delete_other_users_review(
        self, api_client, authenticate_client, create_review, create_user, create_order
    ):
        user1 = authenticate_client()
        user2 = create_user("another_reviewer_delete@example.com", "pass123")
        order = create_order(user=user2)
        review = create_review(order=order, reviewer=user2)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete_any_review(
        self, api_client, authenticate_client, create_review, create_user, create_order
    ):
        admin_user = authenticate_client(is_staff=True)
        user2 = create_user("another_reviewer_delete_admin@example.com", "pass123")
        order = create_order(user=user2)
        review = create_review(order=order, reviewer=user2)
        url = reverse("review:review-detail", kwargs={"pk": review.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Review.objects.filter(pk=review.pk).exists()
