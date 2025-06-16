from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.image.models import Image
from apps.image.utils import delete_from_cloudinary, upload_to_cloudinary
from utils.exceptions import CustomAPIException
from utils.profanity_filter import ProfanityFilter
from utils.responses.user import (
    DUPLICATE_EMAIL,
    DUPLICATE_NICKNAME,
    INVALID_REFRESH_TOKEN,
    SIGNUP_PASSWORD_MISMATCH,
)

User = get_user_model()
profanity_filter = ProfanityFilter()


class UsernameSerializer(serializers.ModelSerializer):
    """사용자 이름 시리얼라이저."""

    class Meta:
        model = User
        fields = ["id", "username"]


class PasswordValidator:
    @staticmethod
    def validate_password(password):
        if len(password) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not any(c.isupper() for c in password):
            raise serializers.ValidationError("비밀번호는 최소 하나의 대문자를 포함해야 합니다.")
        if not any(c.islower() for c in password):
            raise serializers.ValidationError("비밀번호는 최소 하나의 소문자를 포함해야 합니다.")
        if not any(c.isdigit() for c in password):
            raise serializers.ValidationError("비밀번호는 최소 하나의 숫자를 포함해야 합니다.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise serializers.ValidationError("비밀번호는 최소 하나의 특수문자를 포함해야 합니다.")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message=DUPLICATE_EMAIL["message"])]
    )
    nickname = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all(), message=DUPLICATE_NICKNAME["message"])]
    )

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "name", "nickname", "phone"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(SIGNUP_PASSWORD_MISMATCH)

        PasswordValidator.validate_password(data["password"])

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(DUPLICATE_EMAIL)

        if User.objects.filter(nickname=data["nickname"]).exists():
            raise serializers.ValidationError(DUPLICATE_NICKNAME)

        if profanity_filter.contains_profanity(data["name"]):
            raise serializers.ValidationError("이름에 부적절한 단어가 포함되어 있습니다.")

        if profanity_filter.contains_profanity(data["nickname"]):
            raise serializers.ValidationError("닉네임에 부적절한 단어가 포함되어 있습니다.")

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)


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


class UserSerializer(serializers.ModelSerializer):
    """기본 사용자 시리얼라이저."""

    user_type_display = serializers.CharField(source="get_user_type_display", read_only=True)
    user_grade_display = serializers.CharField(source="get_user_grade_display", read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "nickname",
            "phone",
            "user_type",
            "user_type_display",
            "user_grade",
            "user_grade_display",
            "is_active",
            "is_email_verified",
            "image_url",
            "created_at",
        ]
        read_only_fields = ["id", "email", "created_at", "is_email_verified"]

    def get_image_url(self, obj):
        profile_image = obj.profile_images.first()
        if profile_image and profile_image.image_url:
            return profile_image.image_url
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        # 관리자가 아닌 경우 민감한 정보 제거
        if not (request and request.user.is_staff):
            data.pop("phone", None)
            data.pop("is_active", None)
            data.pop("is_email_verified", None)

        return data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    profile_image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "name",
            "nickname",
            "phone",
            # "profile_image", # GenericRelation이므로 직접 필드에 포함하지 않습니다.
        ]

    def validate_name(self, value):
        if profanity_filter.contains_profanity(value):
            raise serializers.ValidationError("이름에 부적절한 단어가 포함되어 있습니다.")
        return value

    def validate_nickname(self, value):
        instance = self.instance
        if instance and instance.nickname != value and User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("닉네임이 이미 존재합니다.")
        if profanity_filter.contains_profanity(value):
            raise serializers.ValidationError("닉네임에 부적절한 단어가 포함되어 있습니다.")
        return value

    def update(self, instance, validated_data):
        profile_image_file = validated_data.pop("profile_image_file", None)

        # 프로필 이미지 처리
        if profile_image_file is not None:  # 새로운 이미지가 제공되었거나 이미지를 제거하려는 경우
            current_profile_image = instance.profile_images.first()

            if current_profile_image:  # 기존 이미지가 있다면 Cloudinary와 DB에서 삭제
                delete_from_cloudinary(current_profile_image.public_id)
                current_profile_image.delete()

            if profile_image_file:  # 새로운 파일이 실제로 제공된 경우 (None이 아닌 경우)
                # Cloudinary에 새 이미지 업로드
                uploaded_data = upload_to_cloudinary(profile_image_file, folder="profile_images")
                Image.objects.create(
                    content_object=instance,
                    image_url=uploaded_data["secure_url"],
                    public_id=uploaded_data["public_id"],
                    content_type=ContentType.objects.get_for_model(User),
                )
        elif "profile_image_file" in self.initial_data and self.initial_data["profile_image_file"] is None:
            # 사용자가 명시적으로 profile_image_file=null을 보내 이미지를 제거하려는 경우
            current_profile_image = instance.profile_images.first()
            if current_profile_image:
                delete_from_cloudinary(current_profile_image.public_id)
                current_profile_image.delete()

        return super().update(instance, validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    profile_image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "email",
            "name",
            "nickname",
            "phone",
            "user_type",
            "user_grade",
            "is_active",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if profanity_filter.contains_profanity(value):
            raise serializers.ValidationError("이름에 부적절한 단어가 포함되어 있습니다.")
        return value

    def validate_email(self, value):
        instance = self.instance
        if instance and instance.email != value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이메일이 이미 존재합니다.")
        return value

    def validate_nickname(self, value):
        instance = self.instance
        if instance and instance.nickname != value and User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("닉네임이 이미 존재합니다.")
        if profanity_filter.contains_profanity(value):
            raise serializers.ValidationError("닉네임에 부적절한 단어가 포함되어 있습니다.")
        return value

    def update(self, instance, validated_data):
        profile_image_file = validated_data.pop("profile_image_file", None)

        # 프로필 이미지 처리
        if profile_image_file is not None:  # 새로운 이미지가 제공되었거나 이미지를 제거하려는 경우
            current_profile_image = instance.profile_images.first()

            if current_profile_image:  # 기존 이미지가 있다면 Cloudinary와 DB에서 삭제
                delete_from_cloudinary(current_profile_image.public_id)
                current_profile_image.delete()

            if profile_image_file:  # 새로운 파일이 실제로 제공된 경우 (None이 아닌 경우)
                # Cloudinary에 새 이미지 업로드
                uploaded_data = upload_to_cloudinary(profile_image_file, folder="profile_images")
                Image.objects.create(
                    content_object=instance,
                    image_url=uploaded_data["secure_url"],
                    public_id=uploaded_data["public_id"],
                    content_type=ContentType.objects.get_for_model(User),
                )
        elif "profile_image_file" in self.initial_data and self.initial_data["profile_image_file"] is None:
            # 사용자가 명시적으로 profile_image_file=null을 보내 이미지를 제거하려는 경우
            current_profile_image = instance.profile_images.first()
            if current_profile_image:
                delete_from_cloudinary(current_profile_image.public_id)
                current_profile_image.delete()

        request_user = self.context.get("request").user

        # Only staff can change user_type, user_grade, is_active, is_staff, is_superuser
        if not request_user.is_staff:
            restricted_fields = [
                "user_type",
                "user_grade",
                "is_active",
                "is_staff",
                "is_superuser",
            ]
            for field in restricted_fields:
                if field in validated_data and getattr(instance, field) != validated_data[field]:
                    raise serializers.ValidationError(f"'{field}' 필드를 변경할 권한이 없습니다.")

        # If staff, but not superuser, prevent changing is_staff and is_superuser
        if request_user.is_staff and not request_user.is_superuser:
            if "is_staff" in validated_data and getattr(instance, "is_staff") != validated_data["is_staff"]:
                raise serializers.ValidationError("is_staff 필드를 변경할 권한이 없습니다.")
            if "is_superuser" in validated_data and getattr(instance, "is_superuser") != validated_data["is_superuser"]:
                raise serializers.ValidationError("is_superuser 필드를 변경할 권한이 없습니다.")

        return super().update(instance, validated_data)


class PasswordCheckSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    token = serializers.CharField()

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("해당 이메일로 등록된 사용자가 없습니다.")
        return value


class UserBulkApproveSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1, error_messages={"min_value": "유효한 사용자 ID여야 합니다."}),
        min_length=1,
        error_messages={"min_length": "최소 하나 이상의 사용자 ID가 필요합니다."},
    )


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context["request"].user

        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")

        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")

        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError("새 비밀번호는 현재 비밀번호와 달라야 합니다.")

        PasswordValidator.validate_password(data["new_password"])

        return data

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
