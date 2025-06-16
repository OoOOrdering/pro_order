from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.order.models import Order
from apps.progress.models import Progress
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
def create_progress(db, create_order, create_user):
    def _create_progress(order, last_updated_by=None, **kwargs):
        if last_updated_by is None:
            last_updated_by = create_user("admin_for_progress@test.com", "password", is_staff=True)
        return Progress.objects.create(
            order=order,
            status=Progress.STATUS_CHOICES[0][0],
            current_step="Initial Step",
            last_updated_by=last_updated_by,
            **kwargs,
        )

    return _create_progress


@pytest.mark.django_db
class TestProgressAPI:
    def test_create_progress(self, api_client, authenticate_client, create_order):
        user = authenticate_client(is_staff=True)
        order = create_order(user=user)
        url = reverse("progress:progress-list-create")
        data = {
            "order": order.pk,
            "status": "in_progress",
            "current_step": "Design Phase",
            "notes": "Starting design process.",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Progress.objects.count() == 1
        assert response.data["status"] == "in_progress"

    def test_get_progress_list(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order1 = create_order(user=create_user("user1@test.com", "pass"))
        order2 = create_order(user=create_user("user2@test.com", "pass"))
        create_progress(order=order1, status="pending")
        create_progress(order=order2, status="completed")
        url = reverse("progress:progress-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_progress_by_status(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order1 = create_order(user=create_user("user3@test.com", "pass"))
        order2 = create_order(user=create_user("user4@test.com", "pass"))
        create_progress(order=order1, status="pending")
        create_progress(order=order2, status="completed")
        url = reverse("progress:progress-list-create") + "?status=completed"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "completed"

    def test_filter_progress_by_date_range(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order = create_order(user=user)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        progress = create_progress(order=order, estimated_completion_date=today)

        url = (
            reverse("progress:progress-list-create")
            + f"?estimated_completion_date__gte={yesterday}&estimated_completion_date__lte={tomorrow}"
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == progress.pk

    def test_search_progress(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order1 = create_order(user=create_user("user5@test.com", "pass"), order_number="PROG-ORD-001")
        order2 = create_order(user=create_user("user6@test.com", "pass"), order_number="PROG-ORD-002")
        create_progress(order=order1, notes="Progress for order 001")
        create_progress(order=order2, notes="Progress for order 002")

        # 주문 번호로 검색
        url = reverse("progress:progress-list-create") + "?search=001"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["order"]["order_number"] == "PROG-ORD-001"

        # 비고 내용으로 검색
        url = reverse("progress:progress-list-create") + "?search=Progress for order 002"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["notes"] == "Progress for order 002"

    def test_sort_progress(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order1 = create_order(user=user)
        order2 = create_order(user=user)

        # 다른 상태의 진행 상황 생성
        progress1 = create_progress(order=order1, status="pending")
        progress2 = create_progress(order=order2, status="completed")

        # 상태별 정렬
        url = reverse("progress:progress-list-create") + "?ordering=status"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["status"] == "completed"
        assert response.data["results"][1]["status"] == "pending"

    def test_get_progress_detail(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order = create_order(user=user)
        progress = create_progress(order=order)
        url = reverse("progress:progress-detail", kwargs={"pk": progress.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == progress.pk
        assert response.data["status"] == progress.status

    def test_update_progress(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order = create_order(user=user)
        progress = create_progress(order=order)
        url = reverse("progress:progress-detail", kwargs={"pk": progress.pk})
        updated_data = {
            "status": "completed",
            "actual_completion_date": timezone.now().isoformat().split("T")[0],
        }
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        progress.refresh_from_db()
        assert progress.status == "completed"
        assert progress.actual_completion_date is not None

    def test_delete_progress(
        self,
        api_client,
        authenticate_client,
        create_progress,
        create_order,
        create_user,
    ):
        user = authenticate_client(is_staff=True)
        order = create_order(user=user)
        progress = create_progress(order=order)
        url = reverse("progress:progress-detail", kwargs={"pk": progress.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Progress.objects.filter(pk=progress.pk).exists()

    def test_unauthorized_access(self, api_client, create_progress, create_order, create_user):
        order = create_order(user=create_user("user7@test.com", "pass"))
        progress = create_progress(order=order)

        # 인증되지 않은 상태에서 API 접근 시도
        url = reverse("progress:progress-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        url = reverse("progress:progress-detail", kwargs={"pk": progress.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
