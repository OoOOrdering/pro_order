from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class WiStarTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    class Meta:
        fields = ["email", "password"]

    def validate(self, attrs):
        # email을 username으로 매핑
        authenticate_kwargs = {
            self.username_field: attrs.get("email"),
            "password": attrs.get("password"),
        }
        print(f"[DEBUG] authenticate_kwargs: {authenticate_kwargs}")
        request = self.context.get("request", None)
        if request is not None:
            self.user = authenticate(request, **authenticate_kwargs)
        else:
            self.user = authenticate(**authenticate_kwargs)
        print(f"[DEBUG] authenticate result: {self.user}, type: {type(self.user)}")
        if self.user:
            print(
                f"[DEBUG] is_active: {getattr(self.user, 'is_active', None)}, is_email_verified: {getattr(self.user, 'is_email_verified', None)}"
            )
        if not self.user:
            raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        # 인증 성공 시 last_login을 직접 갱신
        from django.utils import timezone

        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])
        refresh = self.get_token(self.user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 토큰에 유저 정보를을 함께 담아서 보냄
        token["email"] = user.email
        token["nickname"] = user.nickname
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        return token


# 토큰 정보 확인
# https://jwt.io/
