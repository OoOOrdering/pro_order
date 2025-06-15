import pytest
from django.core import signing
from django.core.signing import TimestampSigner
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        return User.objects.create_user(**kwargs)

    return make_user


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


@pytest.mark.django_db
def test_login(api_client, create_user):
    user = create_user(email="login@example.com", password="qwer1234!", is_active=True)
    url = reverse("user:token_login")
    data = {"email": user.email, "password": "qwer1234!"}
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data["data"]
    assert "csrf_token" in response.data["data"]
    assert "refresh_token" in response.cookies


@pytest.mark.django_db
def test_token_logout(api_client, create_user):
    user = create_user(
        email="token_logout@example.com", password="qwer1234!", is_active=True
    )
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
    user = create_user(
        email="refresh@example.com", password="qwer1234!", is_active=True
    )
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
def test_profile_crud(api_client, create_user):
    user = create_user(
        email="profile@example.com",
        password="qwer1234!",
        name="Old",
        nickname="OldNick",
        is_active=True,
    )
    login_url = reverse("user:token_login")
    login_response = api_client.post(
        login_url, {"email": user.email, "password": "qwer1234!"}
    )
    access_token = login_response.data["data"]["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    url = reverse("user:profile")

    # GET
    res = api_client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data["data"]["nickname"] == "OldNick"

    # PATCH
    res = api_client.patch(url, {"nickname": "NewNick"})
    assert res.status_code == status.HTTP_200_OK
    assert res.data["data"]["nickname"] == "NewNick"

    # DELETE
    res = api_client.delete(url)
    assert res.status_code == status.HTTP_200_OK
    assert User.objects.filter(email=user.email).exists() is False


@pytest.mark.django_db
def test_password_check(api_client, create_user):
    user = create_user(
        email="passcheck@example.com", password="qwer1234!", is_active=True
    )
    login_url = reverse("user:token_login")
    login_response = api_client.post(
        login_url, {"email": user.email, "password": "qwer1234!"}
    )
    access_token = login_response.data["data"]["access_token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    url = reverse("user:password_check")

    # 성공
    res = api_client.post(url, {"password": "qwer1234!"})
    assert res.status_code == status.HTTP_200_OK
    assert res.data["code"] == 200

    # 실패
    res = api_client.post(url, {"password": "wrongpass"})
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.data["code"] == 400
