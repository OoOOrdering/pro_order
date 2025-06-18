from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User

from .models import Order, OrderItem


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
    def _authenticate_client(is_staff=False):
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
def create_order(create_user):
    def _create_order(user, **kwargs):
        order = Order.objects.create(
            user=user,
            order_number=f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S%f')}",
            status=Order.OrderStatus.PENDING,
            total_amount=Decimal("100.00"),
            payment_method="Credit Card",
            payment_status="PAID",
            shipping_address="123 Test St",
            shipping_phone="123-456-7890",
            shipping_name="Test Recipient",
            **kwargs,
        )
        OrderItem.objects.create(
            order=order,
            product_name="Test Product",
            quantity=1,
            price=Decimal("100.00"),
        )
        return order

    return _create_order


@pytest.mark.django_db
class TestOrderAPI:
    def test_create_order(self, api_client, authenticate_client):
        user = authenticate_client()
        url = reverse("order:order-list-create")
        data = {
            "shipping_address": "456 New St",
            "shipping_phone": "098-765-4321",
            "shipping_name": "New Recipient",
            "payment_method": "Bank Transfer",
            "payment_id": "PAYID12345",
            "total_amount": "200.00",
            "items": [{"product_name": "New Product A", "quantity": 2, "price": "100.00"}],
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Order.objects.count() == 1
        assert OrderItem.objects.filter(order__id=response.data["id"]).count() == 1

    def test_get_order_list(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        create_order(user=user, status=Order.OrderStatus.PENDING)
        create_order(user=user, status=Order.OrderStatus.COMPLETED)
        url = reverse("order:order-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_order_list_filtered_by_status(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        create_order(user=user, status=Order.OrderStatus.PENDING)
        create_order(user=user, status=Order.OrderStatus.COMPLETED)
        url = reverse("order:order-list-create") + "?status=PENDING"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == Order.OrderStatus.PENDING

    def test_get_order_list_searched_by_shipping_name(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        create_order(user=user, shipping_name="Alice").save()
        create_order(user=user, shipping_name="Bob").save()
        url = reverse("order:order-list-create") + "?search=Alice"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["shipping_name"] == "Alice"

    def test_get_order_detail(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        url = reverse("order:order-detail", kwargs={"pk": order.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["order_number"] == order.order_number

    def test_update_order(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        url = reverse("order:order-detail", kwargs={"pk": order.pk})
        updated_data = {"shipping_memo": "Fragile item"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.shipping_memo == "Fragile item"

    def test_delete_order(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user)
        url = reverse("order:order-detail", kwargs={"pk": order.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Order.objects.filter(pk=order.pk).exists()

    def test_cancel_order(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user, status=Order.OrderStatus.PENDING)
        url = reverse("order:order-cancel", kwargs={"pk": order.pk})
        response = api_client.post(url, {"cancel_reason": "Customer changed mind"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.OrderStatus.CANCELLED
        assert order.cancel_reason == "Customer changed mind"

    def test_refund_order_by_admin(self, api_client, authenticate_client, create_order):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(
            user=create_user("another@example.com", "pass123"),
            status=Order.OrderStatus.CANCELLED,
        )
        url = reverse("order:order-refund", kwargs={"pk": order.pk})
        response = api_client.post(url, {"refund_reason": "Item out of stock"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.OrderStatus.REFUNDED
        assert order.refund_reason == "Item out of stock"

    def test_non_admin_cannot_refund_order(self, api_client, authenticate_client, create_order):
        user = authenticate_client()
        order = create_order(user=user, status=Order.OrderStatus.CANCELLED)
        url = reverse("order:order-refund", kwargs={"pk": order.pk})
        response = api_client.post(url, {"refund_reason": "Unauthorized"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_order_status_log_created_on_status_change(self, authenticate_client, create_order):
        from apps.order_status_log.models import OrderStatusLog

        user = authenticate_client()
        order = create_order(user=user, status=Order.OrderStatus.PENDING)
        initial_log_count = OrderStatusLog.objects.count()

        order.status = Order.OrderStatus.PROCESSING
        order.save()
        assert OrderStatusLog.objects.count() == initial_log_count + 1
        latest_log = OrderStatusLog.objects.latest("changed_at")
        assert latest_log.order == order
        assert latest_log.status_from == Order.OrderStatus.PENDING
        assert latest_log.status_to == Order.OrderStatus.PROCESSING

        # Test if no log is created when other fields change but status doesn't
        order.shipping_memo = "Updated memo for no log"
        order.save()
        assert OrderStatusLog.objects.count() == initial_log_count + 1  # Should not increase
