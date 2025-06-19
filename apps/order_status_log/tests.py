from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.order.models import Order
from apps.order_status_log.models import OrderStatusLog


@pytest.fixture
def create_order_status_log(db):
    def _create_order_status_log(
        order,
        changed_by,
        previous_status=Order.OrderStatus.PENDING,
        new_status=Order.OrderStatus.PROCESSING,
        reason="Test reason",
        memo="Test memo",
    ):
        return OrderStatusLog.objects.create(
            order=order,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            memo=memo,
        )

    return _create_order_status_log


@pytest.mark.django_db
class TestOrderStatusLogAPI:
    def test_create_order_status_log_by_staff(self, authenticated_client, create_order):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        url = reverse("order_status_log:order-status-log-list-create")
        data = {
            "order": order.pk,
            "new_status": Order.OrderStatus.PROCESSING,
            "reason": "Initial status change",
            "memo": "Processing started",
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert OrderStatusLog.objects.count() == 0
        assert response.data["detail"].startswith("주문 상태 로그는 직접 생성할 수 없습니다")

    def test_create_order_status_log_by_normal_user_fails(self, authenticated_client, create_order):
        client, normal_user = authenticated_client()
        order = create_order(user=normal_user)
        url = reverse("order_status_log:order-status-log-list-create")
        data = {"order": order.pk, "new_status": Order.OrderStatus.PROCESSING, "reason": "Attempt to change status"}
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert OrderStatusLog.objects.count() == 0
        assert response.data["detail"].startswith("주문 상태 로그는 직접 생성할 수 없습니다")

    def test_get_order_status_log_list(self, authenticated_client, create_order, create_order_status_log):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        # Create multiple logs
        create_order_status_log(order=order, changed_by=staff_user)
        create_order_status_log(
            order=order,
            changed_by=staff_user,
            previous_status=Order.OrderStatus.PROCESSING,
            new_status=Order.OrderStatus.COMPLETED,
        )

        url = reverse("order_status_log:order-status-log-list-create")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_order_status_log_detail(self, authenticated_client, create_order, create_order_status_log):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        log = create_order_status_log(order=order, changed_by=staff_user)

        url = reverse("order_status_log:order-status-log-detail", args=[log.pk])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == log.pk
        assert response.data["order"] == order.pk
        assert response.data["memo"] == "Test memo"

    def test_filter_order_status_logs(self, authenticated_client, create_order, create_order_status_log):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)

        # Create logs with different statuses
        create_order_status_log(
            order=order,
            changed_by=staff_user,
            previous_status=Order.OrderStatus.PENDING,
            new_status=Order.OrderStatus.PROCESSING,
        )
        create_order_status_log(
            order=order,
            changed_by=staff_user,
            previous_status=Order.OrderStatus.PROCESSING,
            new_status=Order.OrderStatus.COMPLETED,
        )

        url = reverse("order_status_log:order-status-log-list-create")

        # Filter by new_status
        response = client.get(f"{url}?new_status=COMPLETED")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["new_status"] == Order.OrderStatus.COMPLETED

        # Filter by previous_status
        response = client.get(f"{url}?previous_status=PROCESSING")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["previous_status"] == Order.OrderStatus.PROCESSING

    def test_search_order_status_logs(self, authenticated_client, create_order, create_order_status_log):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)

        # Create log with specific reason and memo
        create_order_status_log(
            order=order, changed_by=staff_user, reason="Customer requested cancellation", memo="Refund processed"
        )

        url = reverse("order_status_log:order-status-log-list-create")

        # Search by reason
        response = client.get(f"{url}?search=cancellation")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "cancellation" in response.data["results"][0]["reason"].lower()

        # Search by memo
        response = client.get(f"{url}?search=refund")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "refund" in response.data["results"][0]["memo"].lower()

    def test_order_status_log_ordering(self, authenticated_client, create_order, create_order_status_log):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)

        # Create logs with different timestamps
        log1 = create_order_status_log(order=order, changed_by=staff_user, reason="First status change")
        log2 = create_order_status_log(order=order, changed_by=staff_user, reason="Second status change")

        url = reverse("order_status_log:order-status-log-list-create")

        # Test descending order (default)
        response = client.get(f"{url}?ordering=-created_at")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == log2.id
        assert response.data["results"][1]["id"] == log1.id

        # Test ascending order
        response = client.get(f"{url}?ordering=created_at")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == log1.id
        assert response.data["results"][1]["id"] == log2.id
