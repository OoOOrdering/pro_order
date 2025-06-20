from unittest.mock import patch

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
        "password": "Qwer1234!",
        "password_confirm": "Qwer1234!",
        "nickname": "testuser",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    # assert "verify_url" in response.data["data"]


@pytest.mark.django_db
def test_verify_email(api_client, create_user):
    user = create_user(
        email="verify@example.com", password="1234", is_active=False, is_email_verified=False, nickname="verifyuser"
    )
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
    user = create_user(email="login@example.com", password="Qwer1234!", is_active=True, nickname="loginuser")
    url = reverse("user:token_login")
    data = {"email": user.email, "password": "Qwer1234!"}
    response = api_client.post(url, data)

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]
    assert "refresh_token" in response.cookies
    assert user.last_login is not None


@pytest.mark.django_db
def test_token_logout(api_client, create_user):
    user = create_user(email="token_logout@example.com", password="Qwer1234!", is_active=True, nickname="logoutuser")
    login_url = reverse("user:token_login")
    data = {"email": user.email, "password": "Qwer1234!"}
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
    user = create_user(email="refresh@example.com", password="Qwer1234!", is_active=True, nickname="refreshuser")
    login_url = reverse("user:token_login")
    data = {"email": user.email, "password": "Qwer1234!"}
    login_response = api_client.post(login_url, data)

    refresh_token = login_response.cookies.get("refresh_token").value
    csrf_token = login_response.data["data"]["csrf_token"]
    api_client.cookies["refresh_token"] = refresh_token

    refresh_url = reverse("user:token_refresh")
    response = api_client.post(refresh_url, HTTP_X_CSRFTOKEN=csrf_token)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]


@pytest.mark.django_db
class TestUserAPI(APITestCase):
    def setUp(self):
        # create_user fixture를 사용하려면 setUp 대신 setUpTestData 또는 각 테스트에 fixture 인자를 사용해야 함
        # APITestCase는 pytest fixture를 직접 쓸 수 없으므로, setUpTestData에서 직접 생성
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123!",
            nickname="testuser",
            is_active=True,
            is_email_verified=False,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Adminpass123!",
            nickname="adminuser",
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_email_verified=True,
            role="admin",
        )

    def test_user_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "newuser@example.com",
            "password": "Newpass123!",
            "password_confirm": "Newpass123!",
            "nickname": "newuser",
        }
        with patch("utils.email.send_email_async.delay") as mock_email:
            mock_email.return_value = None
            response = self.client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == 3
        assert User.objects.get(email="newuser@example.com").is_active is False

    def test_email_verification(self):
        # 이메일 인증 토큰 생성
        signer = TimestampSigner()
        signed_email = signer.sign(self.user.email)
        signed_code = signing.dumps(signed_email)

        url = reverse("user:verify_email") + f"?code={signed_code}"
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.is_email_verified is True
        assert self.user.is_active is True

    def test_user_login(self):
        url = reverse("user:token_login")
        data = {"email": "test@example.com", "password": "testpass123!"}
        response = self.client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data["data"]
        assert "csrf_token" in response.data["data"]
        assert "refresh_token" in response.cookies

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

        assert response.status_code == status.HTTP_200_OK
        # 쿠키가 빈 값이거나 아예 없으면 삭제된 것으로 간주
        assert "refresh_token" not in response.cookies or not response.cookies["refresh_token"].value

    def test_user_profile_update(self):
        # 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "test@example.com", "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 프로필 업데이트
        url = reverse("user:user-profile")
        data = {"nickname": "updateduser"}
        response = self.client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.nickname == "updateduser"

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

        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.is_active is False

    def test_admin_user_management(self):
        # 관리자 로그인
        login_url = reverse("user:token_login")
        login_data = {"email": "admin@example.com", "password": "Adminpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 사용자 목록 조회
        url = reverse("user:user-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 2

    def test_password_change(self):
        # self.user의 비밀번호를 명확히 지정
        self.user.set_password("testpass123!")
        self.user.save()
        self.user.refresh_from_db()
        url = reverse("user:password_change")
        data = {
            "old_password": "testpass123!",
            "new_password": "Newpass123!",
            "new_password_confirm": "Newpass123!",
        }
        # 로그인 후 access_token을 받아서 사용
        login_url = reverse("user:token_login")
        login_data = {"email": self.user.email, "password": "testpass123!"}
        login_response = self.client.post(login_url, login_data)
        access_token = login_response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        # 새 비밀번호로 로그인 테스트
        login_data = {"email": self.user.email, "password": "Newpass123!"}
        login_response = self.client.post(login_url, login_data)
        assert login_response.status_code == status.HTTP_200_OK

    def test_duplicate_email_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "test@example.com",
            "password": "newpass123!",
            "password_confirm": "newpass123!",
            "nickname": "newuser",
        }
        response = self.client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_nickname_registration(self):
        url = reverse("user:signup")
        data = {
            "email": "anotheruser@example.com",
            "password": "newpass123!",
            "password_confirm": "newpass123!",
            "nickname": "testuser",
        }
        response = self.client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_email_verification(self):
        # 유효하지 않은 토큰
        url = reverse("user:verify_email") + "?code=invalid_code"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expired_email_verification(self):
        # 만료된 토큰 생성
        signer = TimestampSigner(salt="email_verification")
        signed_email = signer.sign(self.user.email)
        # 만료 시간을 짧게 설정하여 테스트
        signed_code = signing.dumps(signed_email, compress=False, serializer=signing.JSONSerializer)
        with pytest.raises(signing.SignatureExpired):
            signing.loads(signed_code, max_age=0.00000001, serializer=signing.JSONSerializer)  # 즉시 만료

        url = reverse("user:verify_email") + f"?code={signed_code}"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordValidators(APITestCase):
    def test_custom_password_validator_min_length(self):
        validator = CustomPasswordValidator(min_length=10)
        with pytest.raises(ValidationError):
            validator.validate("short", user=None)

    def test_custom_password_validator_no_upper(self):
        validator = CustomPasswordValidator(require_upper=True)
        with pytest.raises(ValidationError):
            validator.validate("password123!", user=None)

    def test_custom_password_validator_no_lower(self):
        validator = CustomPasswordValidator(require_lower=True)
        with pytest.raises(ValidationError):
            validator.validate("PASSWORD123!", user=None)

    def test_custom_password_validator_no_digit(self):
        validator = CustomPasswordValidator(require_digit=True)
        with pytest.raises(ValidationError):
            validator.validate("Password!!", user=None)

    def test_custom_password_validator_no_special(self):
        validator = CustomPasswordValidator(require_special=True)
        with pytest.raises(ValidationError):
            validator.validate("Password123", user=None)

    def test_custom_password_validator_valid(self):
        validator = CustomPasswordValidator(
            min_length=8,
            require_upper=True,
            require_lower=True,
            require_digit=True,
            require_special=True,
        )
        try:
            validator.validate("ValidPass123!", user=None)
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")


@pytest.mark.django_db
def test_create_user_password_check(create_user):
    user = create_user(email="pwtest@example.com", password="Qwer1234!", is_active=True, nickname="pwtestuser")
    assert user.check_password("Qwer1234!") is True
