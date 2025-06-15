from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

from utils.exceptions import CustomAPIException
from utils.responses.user import (
    DUPLICATE_EMAIL,
    DUPLICATE_NICKNAME,
    INVALID_REFRESH_TOKEN,
    SIGNUP_PASSWORD_MISMATCH,
    WEAK_PASSWORD,
)

User = get_user_model()


class UsernameSerializer(serializers.ModelSerializer):
    """사용자 이름 시리얼라이저"""

    class Meta:
        model = User
        fields = ["id", "username"]


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message=DUPLICATE_EMAIL["message"]
            )
        ]
    )
    nickname = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), message=DUPLICATE_NICKNAME["message"]
            )
        ]
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "password_confirm", "name", "nickname"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {
                "write_only": True
            },  # write_only : 쓰기만 되고 읽어 오진 않음.
            # "phone_number": {"required": False, "allow_blank": True}
        }

    # 데이터 검증
    def validate(self, data):
        # 비밀번호 일치 여부 확인
        if data["password"] != data["password_confirm"]:
            raise CustomAPIException(SIGNUP_PASSWORD_MISMATCH)
        data.pop("password_confirm")  # 모델에 없는 필드 제거

        user = User(**data)

        # errors = dict()  # 에러 여러개를 대비한 처리용
        try:
            # validate_password는 settings.py에 AUTH_PASSWORD_VALIDATORS 설정된 조건을 만족하는지 검사
            validate_password(password=data["password"], user=user)
        # 에러 여러개를 대비한 처리
        # except ValidationError as e:
        #     errors['password'] = list(e.messages)
        # if errors:
        #     raise serializers.ValidationError(errors)

        except ValidationError as e:
            weak_password = WEAK_PASSWORD
            weak_password["data"] = list(e.messages)
            raise CustomAPIException(weak_password)

        return super().validate(data)

    def create(self, validated_data):
        # create_user() -> 비밀번호 해싱
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            nickname=validated_data["nickname"],
        )
        return user


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh_token"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)  # 토큰이 유효한지 검사됨
            print(f"토큰 타입: {token.get('token_type')}")  # 디코드된 토큰 타입 확인
            token.blacklist()  # 블랙리스트 등록
        except Exception:
            raise CustomAPIException(INVALID_REFRESH_TOKEN)


class ProfileSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "nickname",
            "email",
            "image_url",
            "created_at",
            "updated_at",
        ]

    def get_image_url(self, obj):
        profile_image = obj.profile_images.first()
        if profile_image and profile_image.image_url:
            # image는 ImageField이기 때문에 .url 속성을 호출하면 저장된 파일의 경로가 자동으로 완전한 URL을 반환
            return profile_image.image_url
        return None


# 결과 예시
# {
#     "id": 1,
#     "name": "홍길동",
#     "nickname": "길동이",
#     "email": "gil@example.com",
#     "profile_image_url": "https://s3.amazonaws.com/your-bucket/uploads/2025/05/09/profile.webp",
#     "profile_thumbnail_url": "https://s3.amazonaws.com/your-bucket/uploads/2025/05/09/profile_thumb.webp"
# }


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password", "name", "nickname"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "password": {
                "write_only": True
            },  # write_only : 쓰기만 되고 읽어 오진 않음.
            # "phone_number": {"required": False, "allow_blank": True}
        }

    def update(self, instance, validated_data):
        if password := validated_data.get("password"):
            validated_data["password"] = make_password(password)

        image_file = validated_data.pop("image", None)
        return super().update(instance, validated_data)


class PasswordCheckSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
