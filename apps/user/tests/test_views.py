import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User


@pytest.fixture(autouse=True)
def setup_admin_user(db, create_user, request):
    if hasattr(request.node, "cls") and request.node.cls.__name__ == "UserListViewTest":
        try:
            request.node.cls.admin = User.objects.get(email="admin@example.com")
        except User.DoesNotExist:
            request.node.cls.admin = create_user(
                email="admin@example.com",
                password="Adminpass123!",
                nickname="admin",
                name="Admin User",
                is_active=True,
                is_email_verified=True,
                is_staff=True,
                is_superuser=True,
            )


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="Test123!@#",
            nickname="testuser",
            name="Test User",
            is_active=True,
            is_email_verified=True,
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user:user-profile")

    def test_get_profile(self):
        """프로필 조회 테스트."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == 200
        assert response.data["data"]["email"] == self.user.email

    def test_update_profile(self):
        """프로필 수정 테스트."""
        data = {"nickname": "new_nickname", "name": "New Name"}
        response = self.client.patch(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == 200
        assert response.data["data"]["nickname"] == "new_nickname"

    def test_delete_profile(self):
        """프로필 삭제(비활성화) 테스트."""
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == 200
        self.user.refresh_from_db()
        assert self.user.is_active is False


class UserListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.get(email="admin@example.com")
        self.url = reverse("user:user-list")

        # 테스트용 일반 사용자 생성
        for i in range(5):
            User.objects.create_user(
                email=f"user{i}@example.com",
                password="Test123!@#",
                nickname=f"user{i}",
                name=f"User {i}",
            )

    def test_list_users(self):
        """사용자 목록 조회 테스트."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == 200
        assert len(response.data["data"]) == 6  # admin + 5 users

    def test_list_users_with_filters(self):
        """필터링된 사용자 목록 조회 테스트."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f"{self.url}?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["code"] == 200

    def test_unauthorized_access(self):
        """권한 없는 접근 테스트."""
        self.client.credentials(HTTP_AUTHORIZATION="")  # 인증 헤더만 제거
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
