from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.faq.models import FAQ
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
def create_faq(db):
    def _create_faq(**kwargs):
        return FAQ.objects.create(
            question=f"Test Question {timezone.now().timestamp()}",
            answer=f"Test Answer {timezone.now().timestamp()}",
            category="General",
            **kwargs,
        )

    return _create_faq


@pytest.mark.django_db
class TestFAQAPI:
    def test_create_faq(self, api_client, authenticate_client):
        admin_user = authenticate_client(is_staff=True)
        url = reverse("faq:faq-list-create")
        data = {
            "question": "How to use the service?",
            "answer": "Here's how to use our service...",
            "category": "Usage",
            "is_published": True,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert FAQ.objects.count() == 1
        assert response.data["question"] == "How to use the service?"

    def test_non_admin_cannot_create_faq(self, api_client, authenticate_client):
        user = authenticate_client(is_staff=False)
        url = reverse("faq:faq-list-create")
        data = {
            "question": "Test Question",
            "answer": "Test Answer",
            "category": "Test",
            "is_published": True,
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_faq_list(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        create_faq(question="FAQ 1", is_published=True)
        create_faq(question="FAQ 2", is_published=True)
        create_faq(question="FAQ 3", is_published=False)

        url = reverse("faq:faq-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_non_admin_sees_only_published_faqs(self, api_client, authenticate_client, create_faq):
        user = authenticate_client(is_staff=False)
        create_faq(question="Published FAQ", is_published=True)
        create_faq(question="Unpublished FAQ", is_published=False)

        url = reverse("faq:faq-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["question"] == "Published FAQ"

    def test_filter_faq_by_category(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        create_faq(question="General FAQ", category="General")
        create_faq(question="Technical FAQ", category="Technical")

        url = reverse("faq:faq-list-create") + "?category=General"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["category"] == "General"

    def test_filter_faq_by_published_status(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        create_faq(question="Published FAQ", is_published=True)
        create_faq(question="Unpublished FAQ", is_published=False)

        url = reverse("faq:faq-list-create") + "?is_published=true"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["question"] == "Published FAQ"

    def test_filter_faq_by_date_range(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        faq = create_faq(question="Date Range Test", created_at=today)

        url = reverse("faq:faq-list-create") + f"?created_at__gte={yesterday.date()}&created_at__lte={tomorrow.date()}"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == faq.pk

    def test_search_faq(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        create_faq(question="How to search?", answer="Use the search bar")
        create_faq(question="Another question", answer="Another answer")

        # 질문으로 검색
        url = reverse("faq:faq-list-create") + "?search=search"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["question"] == "How to search?"

        # 답변으로 검색
        url = reverse("faq:faq-list-create") + "?search=search bar"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["answer"] == "Use the search bar"

    def test_sort_faq(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        create_faq(question="B Question", category="B")
        create_faq(question="A Question", category="A")

        # 카테고리순 정렬
        url = reverse("faq:faq-list-create") + "?ordering=category"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["category"] == "A"
        assert response.data["results"][1]["category"] == "B"

    def test_get_faq_detail(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        faq = create_faq()
        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["question"] == faq.question

    def test_update_faq(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        faq = create_faq()
        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        updated_data = {"question": "Updated Question", "is_published": False}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        faq.refresh_from_db()
        assert faq.question == "Updated Question"
        assert not faq.is_published

    def test_delete_faq(self, api_client, authenticate_client, create_faq):
        admin_user = authenticate_client(is_staff=True)
        faq = create_faq()
        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FAQ.objects.filter(pk=faq.pk).exists()

    def test_non_admin_cannot_update_faq(self, api_client, authenticate_client, create_faq):
        user = authenticate_client(is_staff=False)
        faq = create_faq()
        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        updated_data = {"question": "Attempted Update"}
        response = api_client.patch(url, updated_data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_admin_cannot_delete_faq(self, api_client, authenticate_client, create_faq):
        user = authenticate_client(is_staff=False)
        faq = create_faq()
        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_published_faq_list(self, api_client, create_faq):
        create_faq(question="Published FAQ 1", is_published=True)
        create_faq(question="Published FAQ 2", is_published=True)
        create_faq(question="Unpublished FAQ", is_published=False)

        url = reverse("faq:faq-published-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_unauthorized_access(self, api_client, create_faq):
        faq = create_faq()

        # 인증되지 않은 상태에서 API 접근 시도
        url = reverse("faq:faq-list-create")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK  # 조회는 가능

        url = reverse("faq:faq-detail", kwargs={"pk": faq.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN  # 상세 조회는 관리자만 가능

        # 수정/삭제는 불가능
        response = api_client.patch(url, {"question": "Unauthorized Update"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
