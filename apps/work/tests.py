from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.order.models import Order
from apps.user.models import User
from apps.work.models import Work


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate_client(api_client, user_factory):
    def _authenticate_client(user=None, is_staff=False):
        if user is None:
            user = user_factory(
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
def create_order(user_factory):
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
def create_work():
    def _create_work(order, assignee, **kwargs):
        base_data = {
            "order": order,
            "assignee": assignee,
            "title": f"Work Title {timezone.now().timestamp()}",
            "description": "Work description.",
            "work_type": Work.WorkType.OTHER,
            "status": Work.WorkStatus.PENDING,
        }
        base_data.update(kwargs)
        return Work.objects.create(**base_data)

    return _create_work


@pytest.mark.django_db
class TestWorkAPI:
    def test_create_work_by_admin(self, api_client, authenticate_client, create_order):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        url = reverse("work:work-list-create")
        data = {
            "order": order.pk,
            "title": "Admin Created Work",
            "description": "Description for admin work.",
            "work_type": Work.WorkType.DESIGN,
            "status": Work.WorkStatus.PENDING,
            "due_date": (timezone.now() + timedelta(days=7)).isoformat(),
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Work.objects.count() == 1
        assert response.data["data"]["title"] == "Admin Created Work"
        assert response.data["data"]["assignee"] == admin_user.pk  # Admin is default assignee

    def test_create_work_by_normal_user_fails(self, api_client, authenticate_client, create_order):
        normal_user = authenticate_client(is_staff=False)
        order = create_order(user=normal_user)
        url = reverse("work:work-list-create")
        data = {
            "order": order.pk,
            "title": "Normal User Work",
            "work_type": Work.WorkType.OTHER,
            "status": Work.WorkStatus.PENDING,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_work_list_by_admin(self, api_client, authenticate_client, create_work, create_order, user_factory):
        admin_user = authenticate_client(is_staff=True)
        user1 = user_factory("user1_work@example.com", "pass1")
        user2 = user_factory("user2_work@example.com", "pass2")
        order1 = create_order(user=user1)
        order2 = create_order(user=user2)
        create_work(order=order1, assignee=user1, title="Work for User1")
        create_work(order=order2, assignee=user2, title="Work for User2")

        url = reverse("work:work-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_work_list_by_normal_user_sees_only_assigned_works(
        self,
        api_client,
        authenticate_client,
        create_work,
        create_order,
        user_factory,
    ):
        normal_user = authenticate_client()
        other_user = user_factory("other_work@example.com", "pass")
        order1 = create_order(user=normal_user)
        order2 = create_order(user=other_user)
        work_for_user = create_work(order=order1, assignee=normal_user, title="My Work")
        work_for_other = create_work(order=order2, assignee=other_user, title="Other's Work")

        url = reverse("work:work-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == work_for_user.pk

    def test_filter_work_by_status(self, api_client, authenticate_client, create_work, create_order, user_factory):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        create_work(
            order=order,
            assignee=admin_user,
            status=Work.WorkStatus.PENDING,
            title="Pending Work",
        )
        create_work(
            order=order,
            assignee=admin_user,
            status=Work.WorkStatus.COMPLETED,
            title="Completed Work",
        )

        url = reverse("work:work-list-create") + f"?status={Work.WorkStatus.COMPLETED}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["status"] == Work.WorkStatus.COMPLETED

    def test_search_work_by_title(self, api_client, authenticate_client, create_work, create_order, user_factory):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        create_work(order=order, assignee=admin_user, title="Searchable Work Title")
        create_work(order=order, assignee=admin_user, title="Another Work")

        url = reverse("work:work-list-create") + "?search=Searchable"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Searchable Work Title"

    def test_sort_work_by_due_date(self, api_client, authenticate_client, create_work, create_order, user_factory):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        work1 = create_work(
            order=order,
            assignee=admin_user,
            title="Work A",
            due_date=timezone.now() + timedelta(days=5),
        )
        work2 = create_work(
            order=order,
            assignee=admin_user,
            title="Work B",
            due_date=timezone.now() + timedelta(days=10),
        )

        url = reverse("work:work-list-create") + "?ordering=due_date"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["id"] == work1.pk
        assert response.data["results"][1]["id"] == work2.pk

    def test_update_work_by_admin(self, api_client, authenticate_client, create_work, create_order):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        work = create_work(order=order, assignee=admin_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        updated_data = {
            "title": "Updated Work Title",
            "status": Work.WorkStatus.COMPLETED,
        }
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        work.refresh_from_db()
        assert work.title == "Updated Work Title"
        assert work.status == Work.WorkStatus.COMPLETED
        assert work.completed_at is not None

    def test_update_work_by_assignee(self, api_client, authenticate_client, create_work, create_order):
        assignee_user = authenticate_client(is_staff=False)
        order = create_order(user=assignee_user)
        work = create_work(order=order, assignee=assignee_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        updated_data = {"status": Work.WorkStatus.IN_PROGRESS}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        work.refresh_from_db()
        assert work.status == Work.WorkStatus.IN_PROGRESS

    def test_normal_user_cannot_update_other_users_work(
        self,
        api_client,
        authenticate_client,
        create_work,
        create_order,
        user_factory,
    ):
        normal_user = authenticate_client(is_staff=False)
        other_user = user_factory("other_assignee@example.com", "pass")
        order = create_order(user=other_user)
        work = create_work(order=order, assignee=other_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        updated_data = {"title": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_delete_work_by_admin(self, api_client, authenticate_client, create_work, create_order):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        work = create_work(order=order, assignee=admin_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Work.objects.filter(pk=work.pk).exists()

    def test_delete_work_by_assignee(self, api_client, authenticate_client, create_work, create_order):
        assignee_user = authenticate_client(is_staff=False)
        order = create_order(user=assignee_user)
        work = create_work(order=order, assignee=assignee_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_normal_user_cannot_delete_other_users_work(
        self,
        api_client,
        authenticate_client,
        create_work,
        create_order,
        user_factory,
    ):
        normal_user = authenticate_client(is_staff=False)
        other_user = user_factory("another_assignee@example.com", "pass")
        order = create_order(user=other_user)
        work = create_work(order=order, assignee=other_user)
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        response = api_client.delete(url)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_completed_at_reset_on_status_change_from_completed(
        self,
        api_client,
        authenticate_client,
        create_work,
        create_order,
    ):
        admin_user = authenticate_client(is_staff=True)
        order = create_order(user=admin_user)
        work = create_work(
            order=order,
            assignee=admin_user,
            status=Work.WorkStatus.COMPLETED,
            completed_at=timezone.now(),
        )
        url = reverse("work:work-detail", kwargs={"pk": work.pk})
        updated_data = {"status": Work.WorkStatus.IN_PROGRESS}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        work.refresh_from_db()
        assert work.status == Work.WorkStatus.IN_PROGRESS
        assert work.completed_at is None
