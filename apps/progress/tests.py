from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from apps.order.models import Order
from apps.progress.models import Progress


@pytest.mark.django_db
class TestProgressAPI:
    def test_create_progress(self, authenticated_client, create_order):
        client, user = authenticated_client(is_staff=True)
        order = create_order(user=user)
        url = reverse("progress:progress-list-create")
        data = {
            "order": order.pk,
            "status": "in_progress",
            "current_step": "Design Phase",
            "notes": "Starting design process.",
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Progress.objects.count() == 1
        assert response.data["status"] == "in_progress"

    def test_get_progress_list(self, authenticated_client, create_order, create_progress):
        client, staff_user = authenticated_client(is_staff=True)
        order1 = create_order(user=staff_user)
        order2 = create_order(user=staff_user)

        # Create progress records
        progress1 = create_progress(order=order1, last_updated_by=staff_user)
        progress2 = create_progress(order=order2, last_updated_by=staff_user)

        url = reverse("progress:progress-list-create")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_progress_by_status(self, authenticated_client, create_progress, create_order):
        client, staff_user = authenticated_client(is_staff=True)
        order1 = create_order(user=staff_user)
        order2 = create_order(user=staff_user)
        create_progress(order=order1, status="pending")
        create_progress(order=order2, status="completed")
        url = reverse("progress:progress-list-create") + "?status=completed"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == "completed"

    def test_filter_progress_by_date_range(self, authenticated_client, create_progress, create_order):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        progress = create_progress(order=order, estimated_completion_date=today)

        url = (
            reverse("progress:progress-list-create")
            + f"?estimated_completion_date__gte={yesterday}&estimated_completion_date__lte={tomorrow}"
        )
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == progress.pk

    def test_search_progress(self, authenticated_client, create_progress, create_order):
        client, staff_user = authenticated_client(is_staff=True)
        order1 = create_order(user=staff_user, order_number="PROG-ORD-001")
        order2 = create_order(user=staff_user, order_number="PROG-ORD-002")
        create_progress(order=order1, notes="Progress for order 001")
        create_progress(order=order2, notes="Progress for order 002")

        # 주문 번호로 검색
        url = reverse("progress:progress-list-create") + "?search=001"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["order"]["order_number"] == "PROG-ORD-001"

        # 비고 내용으로 검색
        url = reverse("progress:progress-list-create") + "?search=Progress for order 002"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["notes"] == "Progress for order 002"

    def test_sort_progress(self, authenticated_client, create_progress, create_order):
        client, staff_user = authenticated_client(is_staff=True)
        order1 = create_order(user=staff_user)
        order2 = create_order(user=staff_user)

        # 다른 상태의 진행 상황 생성
        progress1 = create_progress(order=order1, status="pending")
        progress2 = create_progress(order=order2, status="completed")

        # 상태별 정렬
        url = reverse("progress:progress-list-create") + "?ordering=status"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["status"] == "completed"
        assert response.data["results"][1]["status"] == "pending"

    def test_get_progress_detail(self, authenticated_client, create_order, create_progress):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        progress = create_progress(order=order, last_updated_by=staff_user)

        url = reverse("progress:progress-detail", args=[progress.pk])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == progress.pk
        assert response.data["order"] == order.pk

    def test_update_progress(self, authenticated_client, create_order, create_progress):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        progress = create_progress(order=order, last_updated_by=staff_user)

        url = reverse("progress:progress-detail", args=[progress.pk])
        update_data = {
            "status": "completed",
            "current_step": "Final Review",
            "notes": "Project completed successfully",
        }
        response = client.patch(url, update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "completed"
        assert response.data["current_step"] == "Final Review"

    def test_delete_progress(self, authenticated_client, create_order, create_progress):
        client, staff_user = authenticated_client(is_staff=True)
        order = create_order(user=staff_user)
        progress = create_progress(order=order, last_updated_by=staff_user)

        url = reverse("progress:progress-detail", args=[progress.pk])
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Progress.objects.filter(pk=progress.pk).exists()

    def test_non_staff_user_cannot_create_progress(self, authenticated_client, create_order):
        client, user = authenticated_client(is_staff=False)
        order = create_order(user=user)
        url = reverse("progress:progress-list-create")
        data = {
            "order": order.pk,
            "status": "in_progress",
            "current_step": "Design Phase",
            "notes": "Starting design process.",
        }
        response = client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Progress.objects.count() == 0
