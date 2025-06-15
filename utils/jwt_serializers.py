from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class WiStarTokenObtainPairSerializer(TokenObtainPairSerializer):
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
