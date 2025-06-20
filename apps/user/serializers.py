from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

from apps.image.image_utils import delete_from_cloudinary, upload_to_cloudinary
from apps.image.models import Image
from utils.exceptions import CustomAPIException
from utils.profanity_filter import ProfanityFilter
from utils.serializers import BaseSerializer

# Response constants
DUPLICATE_EMAIL = {"code": 400, "message": "이미 존재하는 이메일입니다."}
DUPLICATE_NICKNAME = {"code": 400, "message": "이미 존재하는 닉네임입니다."}
INVALID_REFRESH_TOKEN = {"code": 401, "message": "유효하지 않은 리프레시 토큰입니다."}
SIGNUP_PASSWORD_MISMATCH = {"code": 400, "message": "비밀번호가 일치하지 않습니다."}

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


class RegisterSerializer(BaseSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all(), message=DUPLICATE_EMAIL["message"])],
    )
    nickname = serializers.CharField(
        required=True,
        max_length=10,
        validators=[UniqueValidator(queryset=User.objects.all(), message=DUPLICATE_NICKNAME["message"])],
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "password",
            "password_confirm",
        ]

    def validate(self, data):
        if data.get("password") != data.get("password_confirm"):
            raise serializers.ValidationError(SIGNUP_PASSWORD_MISMATCH)

        PasswordValidator.validate_password(data.get("password"))

        if User.objects.filter(email=data.get("email")).exists():
            raise serializers.ValidationError(DUPLICATE_EMAIL)

        if User.objects.filter(nickname=data.get("nickname")).exists():
            raise serializers.ValidationError(DUPLICATE_NICKNAME)

        if not data.get("nickname"):
            raise serializers.ValidationError({"nickname": "닉네임은 필수 입력 항목입니다."})
        if len(data.get("nickname", "")) > 10:
            raise serializers.ValidationError({"nickname": "닉네임은 최대 10글자까지 입력 가능합니다."})
        if profanity_filter.contains_profanity(data.get("nickname", "")):
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

    def save(self, **kwargs):  # noqa: ARG002
        try:
            token = RefreshToken(self.token)  # 토큰이 유효한지 검사됨
            if hasattr(token, "blacklist"):
                token.blacklist()  # 블랙리스트 등록
        except Exception as err:
            raise CustomAPIException(INVALID_REFRESH_TOKEN) from err


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
            "nickname",
            "phone",
            "profile_image_file",  # 누락된 필드 추가
            # "profile_image", # GenericRelation이므로 직접 필드에 포함하지 않습니다.
        ]

    def validate_nickname(self, value):
        instance = self.instance
        if instance and instance.nickname != value and User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("닉네임이 이미 존재합니다.")
        if profanity_filter.contains_profanity(value):
            raise serializers.ValidationError("닉네임에 부적절한 단어가 포함되어 있습니다.")
        return value

    def update(self, instance, validated_data):
        profile_image_file = validated_data.pop("profile_image_file", None)

        if profile_image_file:
            # 기존 이미지 모두 삭제 후 새 이미지 업로드
            content_type = ContentType.objects.get_for_model(instance)
            for img in Image.objects.filter(content_type=content_type, object_id=instance.id):
                # Cloudinary에서 이미지 삭제
                if img.public_id:
                    delete_from_cloudinary(img.public_id)
                img.delete()  # DB에서 이미지 객체 삭제

            # 새 이미지 업로드
            image_data = profile_image_file.read()
            image_name = profile_image_file.name
            folder_path = f"users/{instance.id}/profile_image"

            # Cloudinary에 업로드 및 URL/public_id 저장
            try:
                image_url, public_id = upload_to_cloudinary(image_data, image_name, folder_path)
                Image.objects.create(
                    content_object=instance,
                    image_url=image_url,
                    public_id=public_id,
                )
            except Exception as e:
                raise CustomAPIException(f"이미지 업로드 실패: {e}") from e

        return super().update(instance, validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    profile_image_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "email",
            "nickname",
            "phone",
            "user_type",
            "user_grade",
            "is_active",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = ["id"]

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

        if profile_image_file:
            content_type = ContentType.objects.get_for_model(instance)
            for img in Image.objects.filter(content_type=content_type, object_id=instance.id):
                if img.public_id:
                    delete_from_cloudinary(img.public_id)
                img.delete()

            # 새 이미지 업로드
            image_data = profile_image_file.read()
            image_name = profile_image_file.name
            folder_path = f"users/{instance.id}/profile_image"

            # Cloudinary에 업로드 및 URL/public_id 저장
            try:
                image_url, public_id = upload_to_cloudinary(image_data, image_name, folder_path)
                Image.objects.create(
                    content_object=instance,
                    image_url=image_url,
                    public_id=public_id,
                )
            except Exception as e:
                raise CustomAPIException(f"이미지 업로드 실패: {e}") from e

        return super().update(instance, validated_data)


class PasswordCheckSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    token = serializers.CharField()

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        PasswordValidator.validate_password(data["password"])
        return data


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class ResendVerificationEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_active:
                raise serializers.ValidationError("이미 이메일이 인증되었습니다.")
        except User.DoesNotExist as err:
            raise serializers.ValidationError("해당 이메일 주소로 등록된 사용자가 없습니다.") from err
        return value


class UserBulkApproveSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
    )


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("새 비밀번호가 일치하지 않습니다.")
        PasswordValidator.validate_password(data["new_password"])
        return data

    def save(self, **kwargs):  # noqa: ARG002
        user = self.context["request"].user
        if not user.check_password(self.validated_data["old_password"]):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")

        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class NicknameCheckSerializer(serializers.Serializer):
    """닉네임 중복 체크 시리얼라이저"""

    nickname = serializers.CharField(required=True)

    def validate_nickname(self, value):
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError(DUPLICATE_NICKNAME["message"])
        return value
