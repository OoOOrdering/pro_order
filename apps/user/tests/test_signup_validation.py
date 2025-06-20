import pytest
from rest_framework.serializers import ValidationError

from apps.user.serializers import RegisterSerializer


@pytest.mark.django_db
def test_nickname_max_length():
    data = {
        "email": "test1@example.com",
        "password": "Qwer1234!",
        "password_confirm": "Qwer1234!",
        "nickname": "a" * 11,  # 11글자
    }
    with pytest.raises(ValidationError) as exc:
        RegisterSerializer().validate(data)
    assert "닉네임은 최대 10글자까지 입력 가능합니다." in str(exc.value)


@pytest.mark.django_db
def test_nickname_profanity():
    data = {
        "email": "test2@example.com",
        "password": "Qwer1234!",
        "password_confirm": "Qwer1234!",
        "nickname": "욕설닉네임",  # profanity_filter에 걸리는 단어로 가정
    }
    # profanity_filter가 실제로 "욕설"을 필터링하도록 설정되어 있어야 함
    with pytest.raises(ValidationError) as exc:
        RegisterSerializer().validate(data)
    assert "닉네임에 부적절한 단어가 포함되어 있습니다." in str(exc.value)
