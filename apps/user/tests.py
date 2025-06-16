from datetime import timedelta

import pytest
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.user.models import User
from apps.user.validators import CustomPasswordValidator


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email=None, password="testpass123!", **kwargs):
        if email is None:
            email = f"test_user_{timezone.now().timestamp()}@example.com"
        return User.objects.create_user(email=email, password=password, **kwargs)

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


@pytest.mark.django_db
def test_signup_user(api_client):
    url = reverse("user:signup")
    data = {
        "email": "test@example.com",
        "password": "qwer1234!",
        "password_confirm": "qwer1234!",
        "nickname": "testuser",
        "name": "테스트",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    # assert "verify_url" in response.data["data"]


@pytest.mark.django_db
def test_verify_email(api_client, create_user):
    user = create_user(email="verify@example.com", password="1234", is_active=False)
    signer = TimestampSigner()
    signed_email = signer.sign(user.email)
    signed_code = signing.dumps(signed_email)
    url = reverse("user:verify_email") + f"?code={signed_code}"

    response = api_client.get(url)
    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert user.is_active is True
    assert user.is_email_verified is True


@pytest.mark.django_db
def test_login(api_client, create_user):
    user = create_user(email="login@example.com", password="qwer1234!", is_active=True)
    url = reverse("user:token_login")
    data = {"email": user.email, "password": "qwer1234!"}
    response = api_client.post(url, data)

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]
    assert "refresh_token" in response.cookies
    assert user.last_login is not None


@pytest.mark.django_db
def test_token_logout(api_client, create_user):
    user = create_user(email="token_logout@example.com", password="qwer1234!", is_active=True)
    login_url = reverse("user:token_login")
    data = {"email": user.email, "password": "qwer1234!"}
    login_response = api_client.post(login_url, data)

    refresh_token = login_response.cookies.get("refresh_token").value
    access_token = login_response.data["data"]["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    api_client.cookies["refresh_token"] = refresh_token

    token_logout_url = reverse("user:token_logout")
    response = api_client.post(token_logout_url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_token_refresh(api_client, create_user):
    user = create_user(email="refresh@example.com", password="qwer1234!", is_active=True)
    login_url = reverse("user:token_login")
    data = {"email": user.email, "password": "qwer1234!"}
    login_response = api_client.post(login_url, data)

    refresh_token = login_response.cookies.get("refresh_token").value
    csrf_token = login_response.data["data"]["csrf_token"]
    api_client.cookies["refresh_token"] = refresh_token

    refresh_url = reverse("user:token_refresh")
    response = api_client.post(refresh_url, **{"HTTP_X_CSRFTOKEN": csrf_token})

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]


@pytest.mark.django_db
class TestUserAPI(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            name="Test User",
            nickname="testuser",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpass123!",
            name="Admin User",
            nickname="adminuser",
            is_staff=True,
        )

    def test_user_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "newuser@example.com",
            "password": "newpass123!",
            "password_confirm": "newpass123!",
            "name": "New User",
            "nickname": "newuser",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertFalse(User.objects.get(email="newuser@example.com").is_active)

    def test_email_verification(self):
        # 이메일 인증 토큰 생성
        signer = TimestampSigner()
        signed_email = signer.sign(self.user.email)
        signed_code = signing.dumps(signed_email)

        url = reverse("user:verify_email") + f"?code={signed_code}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_active)

    def test_user_login(self):
        url = reverse("user:token_login")
        data = {"email": "test@example.com", "password": "testpass123!"}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data["data"])
        self.assertIn("csrf_token", response.data["data"])
        self.assertIn("refresh_token", response.cookies)

    def test_user_logout(self):
        # 먼저 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "test@example.com", "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 로그아웃
        logout_url = reverse("user:token_logout")
        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("refresh_token", response.cookies)

    def test_user_profile_update(self):
        # 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "test@example.com", "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 프로필 업데이트
        url = reverse("user:user-profile")
        data = {"name": "Updated Name", "nickname": "updateduser"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.nickname, "updateduser")

    def test_user_deactivation(self):
        # 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "test@example.com", "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 계정 비활성화
        url = reverse("user:user-profile")
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_admin_user_management(self):
        # 관리자 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "admin@example.com", "password": "adminpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 사용자 목록 조회
        url = reverse("user:user-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)

    def test_password_change(self):
        # 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "test@example.com", "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 비밀번호 변경
        url = reverse("user:password_change")
        data = {
            "old_password": "testpass123!",
            "new_password": "newpass123!",
            "new_password_confirm": "newpass123!",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 새 비밀번호로 로그인 테스트
        login_data = {"email": "test@example.com", "password": "newpass123!"}
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_duplicate_email_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "test@example.com",  # 이미 존재하는 이메일
            "password": "newpass123!",
            "password_confirm": "newpass123!",
            "name": "New User",
            "nickname": "newuser",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_nickname_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "newuser@example.com",
            "password": "newpass123!",
            "password_confirm": "newpass123!",
            "name": "New User",
            "nickname": "testuser",  # 이미 존재하는 닉네임
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_verification(self):
        # 유효하지 않은 토큰
        url = reverse("user:verify_email") + "?code=invalid_code"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_email_verification(self):
        # 만료된 토큰 생성
        signer = TimestampSigner(salt="user_email_verification")
        signed_email = signer.sign(self.user.email)

        # 수동으로 만료 시간 변경 (예: 2일 전)
        expired_timestamp = (timezone.now() - timedelta(days=2)).timestamp()
        signed_code = f"{signed_email}:{expired_timestamp}"

        url = reverse("user:verify_email") + f"?code={signed_code}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)


@pytest.mark.django_db
class TestPasswordValidators(APITestCase):
    def test_custom_password_validator_min_length(self):
        validator = CustomPasswordValidator(min_length=12)
        with self.assertRaisesMessage(ValidationError, "비밀번호는 최소 12자 이상이어야 합니다."):
            validator.validate("shortpass")

    def test_custom_password_validator_no_upper(self):
        validator = CustomPasswordValidator()
        with self.assertRaisesMessage(ValidationError, "비밀번호는 하나 이상의 대문자를 포함해야 합니다."):
            validator.validate("testpassword123!")

    def test_custom_password_validator_no_lower(self):
        validator = CustomPasswordValidator()
        with self.assertRaisesMessage(ValidationError, "비밀번호는 하나 이상의 소문자를 포함해야 합니다."):
            validator.validate("TESTPASSWORD123!")

    def test_custom_password_validator_no_digit(self):
        validator = CustomPasswordValidator()
        with self.assertRaisesMessage(ValidationError, "비밀번호는 하나 이상의 숫자를 포함해야 합니다."):
            validator.validate("Testpassword!!")

    def test_custom_password_validator_no_special(self):
        validator = CustomPasswordValidator()
        with self.assertRaisesMessage(ValidationError, "비밀번호는 하나 이상의 특수 문자를 포함해야 합니다."):
            validator.validate("Testpassword123")

    def test_custom_password_validator_valid(self):
        validator = CustomPasswordValidator()
        # 유효성 검사 통과 시 예외가 발생하지 않아야 함
        try:
            validator.validate("Testpassword123!")
        except ValidationError as e:
            self.fail(f"유효한 비밀번호에 대해 ValidationError 발생: {e}")
