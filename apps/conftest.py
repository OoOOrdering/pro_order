import os
import uuid
from typing import Any, Callable, Dict, Optional, Tuple
from unittest.mock import MagicMock, patch

# 테스트 모드 설정을 가장 먼저
os.environ["DJANGO_TESTING"] = "True"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
import factory
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from faker import Faker
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.chat_room.models import ChatRoom
from apps.cs_post.models import CSPost
from apps.order.models import Order
from apps.preset_message.models import PresetMessage
from apps.progress.models import Progress
from apps.user.throttles import LoginAttemptThrottle

fake = Faker()

# Django 설정을 로드
django.setup()

# 캐시 관련 설정 오버라이드
TESTING_CACHE_CONFIG = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "OPTIONS": {"IGNORE_EXCEPTIONS": True},
    }
}


@pytest.fixture(autouse=True)
def override_cache_settings():
    """캐시 설정을 테스트용으로 오버라이드합니다."""
    original_cache = getattr(settings, "CACHES", {})
    settings.CACHES = TESTING_CACHE_CONFIG
    yield
    settings.CACHES = original_cache


@pytest.fixture(autouse=True)
def clear_cache():
    """각 테스트 전후로 캐시를 초기화합니다."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def disable_throttling():
    """테스트 환경에서 모든 Throttling을 비활성화합니다."""
    throttle_classes = [
        UserRateThrottle,
        AnonRateThrottle,
        LoginAttemptThrottle,
    ]

    patches = []
    for throttle_class in throttle_classes:
        # allow_request와 get_rate만 패치
        patches.extend(
            [
                patch.object(throttle_class, "allow_request", return_value=True),
                patch.object(throttle_class, "get_rate", return_value=None),
            ]
        )

    for p in patches:
        p.start()

    yield

    for p in patches:
        p.stop()


@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture
def auth_headers(user_factory):
    """인증에 필요한 헤더를 반환하는 fixture"""
    user = user_factory()
    token = getattr(user, "token", None)
    if token:
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
    return {}


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    nickname = factory.Faker("user_name")
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if extracted:
            obj.set_password(extracted)
            obj.save(update_fields=["password"])


@pytest.fixture
def user_factory(db):
    """
    User 인스턴스를 동적으로 생성하는 factory fixture
    예시: user = user_factory(email="test@example.com") 또는 user_factory("test@example.com", "pw")
    """

    def create_user(*args, **kwargs):
        import uuid  # nickname/email 기본값 생성에 사용

        # positional: (email, password)
        if args:
            if len(args) > 0:
                kwargs["email"] = args[0]
            if len(args) > 1:
                kwargs["password"] = args[1]
        if "nickname" not in kwargs or kwargs["nickname"] is None:
            kwargs["nickname"] = f"testuser_{uuid.uuid4().hex[:8]}"
        if "email" not in kwargs or kwargs["email"] is None:
            kwargs["email"] = f"user_{uuid.uuid4().hex[:8]}@example.com"
        # is_staff=True면 role도 admin으로 자동 지정
        if kwargs.get("is_staff"):
            kwargs["role"] = "admin"
        # 테스트 기본값: 활성화 및 이메일 인증 True
        if "is_active" not in kwargs:
            kwargs["is_active"] = True
        if "is_email_verified" not in kwargs:
            kwargs["is_email_verified"] = True
        return UserFactory.create(**kwargs)

    return create_user


@pytest.fixture
def authenticated_client(user_factory) -> Callable[..., Tuple[APIClient, object]]:
    """
    인증된 APIClient와 사용자 객체를 반환하는 fixture
    """

    def _authenticated_client(
        email: Optional[str] = None,
        password: str = "Test1234!",
        nickname: Optional[str] = None,
        is_staff: bool = False,
        **kwargs,
    ) -> Tuple[APIClient, object]:
        user = user_factory(email=email, password=password, nickname=nickname, is_staff=is_staff, **kwargs)
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    return _authenticated_client


@pytest.fixture
def create_chat_room(user_factory):
    """
    채팅방을 생성하는 fixture (creator 필수)
    """

    def _create_chat_room(creator=None, **kwargs):
        if creator is None:
            creator = user_factory()
        chat_room_data = {
            "title": kwargs.get("title", fake.sentence()),
            "description": kwargs.get("description", fake.text()),
            "creator": creator,
            **kwargs,
        }
        return ChatRoom.objects.create(**chat_room_data)

    return _create_chat_room


@pytest.fixture
def chat_room(create_chat_room, user_factory):
    """
    기본 채팅방을 반환하는 fixture (creator 자동 생성)
    """
    return create_chat_room(creator=user_factory())


@pytest.fixture
def cs_post(user_factory):
    """
    테스트용 고객센터 게시글을 생성하는 fixture
    """

    def _create_cs_post(**kwargs):
        user = kwargs.get("user") or user_factory()
        title = kwargs.get("title", fake.sentence())
        content = kwargs.get("content", fake.text())

        return CSPost.objects.create(user=user, title=title, content=content)

    return _create_cs_post


@pytest.fixture
def create_order():
    """Create an order for testing."""

    def _create_order(**kwargs):
        order_data = {
            "order_number": kwargs.pop("order_number", f"ORD-{fake.unique.random_int(min=10000, max=99999)}"),
            "status": kwargs.pop("status", "PENDING"),
            "total_amount": kwargs.pop("total_amount", "100.00"),
            "payment_method": kwargs.pop("payment_method", "Credit Card"),
            "payment_status": kwargs.pop("payment_status", "PAID"),
            "shipping_address": kwargs.pop("shipping_address", fake.address()),
            "shipping_phone": kwargs.pop("shipping_phone", fake.phone_number()),
            "shipping_name": kwargs.pop("shipping_name", fake.name()),
            "shipping_memo": kwargs.pop("shipping_memo", ""),
            **kwargs,
        }
        return Order.objects.create(**order_data)

    return _create_order


@pytest.fixture
def create_preset_message():
    """Create a preset message for testing."""

    def _create_preset_message(**kwargs):
        preset_message_data = {
            "title": kwargs.pop("title", "Default Preset Message"),
            "content": kwargs.pop("content", "Hello, this is a test preset message."),
            "is_active": kwargs.pop("is_active", True),
            **kwargs,
        }
        return PresetMessage.objects.create(**preset_message_data)

    return _create_preset_message


@pytest.fixture
def create_progress():
    """Create a progress record for testing."""

    def _create_progress(**kwargs):
        progress_data = {
            "status": kwargs.pop("status", "pending"),
            "current_step": kwargs.pop("current_step", "Initial Step"),
            "notes": kwargs.pop("notes", "Test progress notes"),
            **kwargs,
        }
        return Progress.objects.create(**progress_data)

    return _create_progress


@pytest.fixture
def create_user(user_factory):
    """
    기존 테스트에서 사용되는 create_user fixture를 user_factory로 alias합니다.
    positional argument(email, password)도 지원합니다.
    """

    def _create_user(*args, **kwargs):
        # positional: (email, password)
        if args:
            if len(args) > 0:
                kwargs["email"] = args[0]
            if len(args) > 1:
                kwargs["password"] = args[1]
        return user_factory(**kwargs)

    return _create_user


@pytest.fixture
def another_user(user_factory):
    """채팅방 등에서 인증되지 않은 다른 사용자 fixture"""
    return user_factory()


@pytest.fixture(autouse=True)
def mock_send_email_async():
    """Celery 이메일 비동기 전송을 mock 처리합니다."""
    with patch("utils.email.send_email_async.delay", return_value=None):
        yield
