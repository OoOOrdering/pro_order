from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="Test123!@#",
            nickname="testuser",
            name="Test User",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user:user-profile")

    def test_get_profile(self):
        """프로필 조회 테스트."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    def test_update_profile(self):
        """프로필 수정 테스트."""
        data = {"nickname": "new_nickname", "name": "New Name"}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(response.data["data"]["nickname"], "new_nickname")

    def test_delete_profile(self):
        """프로필 삭제(비활성화) 테스트."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class UserListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin123!@#",
            nickname="admin",
            name="Admin User",
        )
        self.client.force_authenticate(user=self.admin)
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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)
        self.assertEqual(len(response.data["data"]), 6)  # admin + 5 users

    def test_list_users_with_filters(self):
        """필터링된 사용자 목록 조회 테스트."""
        response = self.client.get(f"{self.url}?is_active=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], 200)

    def test_unauthorized_access(self):
        """권한 없는 접근 테스트."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
