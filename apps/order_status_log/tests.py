from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.order.models import Order
from apps.order_status_log.models import OrderStatusLog
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
def create_order_status_log(db, create_order, create_user):
    def _create_log(order, changed_by, **kwargs):
        return OrderStatusLog.objects.create(
            order=order,
            previous_status=order.status,
            new_status=Order.OrderStatus.PROCESSING,
            reason="Order status changed manually",
            changed_by=changed_by,
            **kwargs,
        )

    return _create_log


@pytest.mark.django_db
class TestOrderStatusLogAPI:
    def test_create_order_status_log_by_staff(self, api_client, authenticate_client, create_order):
        staff_user = authenticate_client(is_staff=True)
        order = create_order(user=staff_user)
        url = reverse("order_status_log:order-status-log-list-create")
        data = {
            "order": order.pk,
            "new_status": "PROCESSING",
            "reason": "Initial status change",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert OrderStatusLog.objects.count() == 1
        assert response.data["new_status"] == "PROCESSING"

    def test_create_order_status_log_by_normal_user_fails(self, api_client, authenticate_client, create_order):
        normal_user = authenticate_client()
        order = create_order(user=normal_user)
        url = reverse("order_status_log:order-status-log-list-create")
        data = {
            "order": order.pk,
            "new_status": "PROCESSING",
            "reason": "Attempt to change status",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_order_status_log_list_by_staff(
        self,
        api_client,
        authenticate_client,
        create_order_status_log,
        create_user,
        create_order,
    ):
        staff_user = authenticate_client(is_staff=True)
        user1 = create_user("user1@example.com", "testpass123!")
        user2 = create_user("user2@example.com", "testpass123!")
        order1 = create_order(user=user1)
        order2 = create_order(user=user2)
        create_order_status_log(order=order1, changed_by=staff_user)
        create_order_status_log(
            order=order2,
            changed_by=staff_user,
            previous_status="PROCESSING",
            new_status="COMPLETED",
        )

        url = reverse("order_status_log:order-status-log-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_order_status_log_list_by_normal_user_sees_only_own_orders(
        self,
        api_client,
        authenticate_client,
        create_order_status_log,
        create_user,
        create_order,
    ):
        normal_user = authenticate_client()
        other_user = create_user("otheruser@example.com", "testpass123!")
        order_for_user = create_order(user=normal_user)
        order_for_other = create_order(user=other_user)
        staff_user = create_user("staff_for_log@example.com", "testpass123!", is_staff=True)

        create_order_status_log(order=order_for_user, changed_by=staff_user)
        create_order_status_log(order=order_for_other, changed_by=staff_user)

        url = reverse("order_status_log:order-status-log-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["order"] == order_for_user.pk

    def test_filter_order_status_log_by_new_status(
        self, api_client, authenticate_client, create_order_status_log, create_order
    ):
        staff_user = authenticate_client(is_staff=True)
        order1 = create_order(user=staff_user, status=Order.OrderStatus.PENDING)
        order2 = create_order(user=staff_user, status=Order.OrderStatus.PENDING)
        log1 = create_order_status_log(order=order1, changed_by=staff_user, new_status=Order.OrderStatus.PROCESSING)
        log2 = create_order_status_log(order=order2, changed_by=staff_user, new_status=Order.OrderStatus.COMPLETED)

        url = reverse("order_status_log:order-status-log-list-create") + "?new_status=PROCESSING"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == log1.pk

    def test_search_order_status_log_by_order_number(
        self, api_client, authenticate_client, create_order_status_log, create_order
    ):
        staff_user = authenticate_client(is_staff=True)
        order1 = create_order(user=staff_user, order_number="ORD-1111")
        order2 = create_order(user=staff_user, order_number="ORD-2222")
        log1 = create_order_status_log(order=order1, changed_by=staff_user, reason="Log for order 1111")
        log2 = create_order_status_log(order=order2, changed_by=staff_user, reason="Log for order 2222")

        url = reverse("order_status_log:order-status-log-list-create") + "?search=1111"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["order"] == order1.pk

    def test_sort_order_status_log_by_created_at(
        self, api_client, authenticate_client, create_order_status_log, create_order
    ):
        staff_user = authenticate_client(is_staff=True)
        order1 = create_order(user=staff_user)
        order2 = create_order(user=staff_user)

        # 시간차를 두고 로그 생성
        log_old = create_order_status_log(
            order=order1,
            changed_by=staff_user,
            created_at=timezone.now() - timedelta(days=2),
        )
        log_new = create_order_status_log(
            order=order2,
            changed_by=staff_user,
            created_at=timezone.now() - timedelta(days=1),
        )

        url = reverse("order_status_log:order-status-log-list-create") + "?ordering=created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == log_old.pk
        assert response.data["results"][1]["id"] == log_new.pk

        url = reverse("order_status_log:order-status-log-list-create") + "?ordering=-created_at"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == log_new.pk
        assert response.data["results"][1]["id"] == log_old.pk

    def test_get_order_status_log_detail_by_staff(
        self, api_client, authenticate_client, create_order_status_log, create_order
    ):
        staff_user = authenticate_client(is_staff=True)
        order = create_order(user=staff_user)
        log = create_order_status_log(order=order, changed_by=staff_user)
        url = reverse("order_status_log:order-status-log-detail", kwargs={"pk": log.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == log.pk

    def test_get_order_status_log_detail_by_normal_user_for_own_order(
        self, api_client, authenticate_client, create_order_status_log, create_order
    ):
        normal_user = authenticate_client()
        order = create_order(user=normal_user)
        staff_user = create_user("staff_for_detail_log@example.com", "testpass123!", is_staff=True)
        log = create_order_status_log(order=order, changed_by=staff_user)

        url = reverse("order_status_log:order-status-log-detail", kwargs={"pk": log.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == log.pk

    def test_get_order_status_log_detail_by_normal_user_for_other_order_fails(
        self,
        api_client,
        authenticate_client,
        create_order_status_log,
        create_user,
        create_order,
    ):
        normal_user = authenticate_client()
        other_user = create_user("other_user_for_detail@example.com", "testpass123!")
        order_for_other = create_order(user=other_user)
        staff_user = create_user("staff_for_other_log@example.com", "testpass123!", is_staff=True)
        log = create_order_status_log(order=order_for_other, changed_by=staff_user)

        url = reverse("order_status_log:order-status-log-detail", kwargs={"pk": log.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND  # 권한이 없으므로 찾을 수 없음
