import random

from config.settings.base import ENV

DEBUG = True
ALLOWED_HOSTS: list[str] = []

# DEBUG = False
# ALLOWED_HOSTS: list[str] = [
#     "127.0.0.1",
#     "localhost",
# ]

# 시크릿 키를 ENV 변수에 저장된 딕셔너리에서 가져옵니다. 만약 파일에서 읽어온 시크릿 키가 존재하지 않는다면 50자리의 무작위 문자열을 반환합니다.
SECRET_KEY: str = ENV.get(
    "DJANGO_SECRET_KEY",
    "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()?", k=50)),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": ENV.get("POSTGRES_HOST", "db"),
        "USER": ENV.get("POSTGRES_USER", "postgres"),
        "PASSWORD": ENV.get("POSTGRES_PASSWORD", "postgres"),
        "NAME": ENV.get("POSTGRES_DB", "oz_collabo"),
        "PORT": ENV.get("POSTGRES_PORT", 5432),
    }
}

import cloudinary

cloudinary.config(
    cloud_name=ENV.get("CLOUD_NAME", "db"),
    api_key=ENV.get("API_KEY", "db"),
    api_secret=ENV.get("API_SECRET", "db"),
    secure=True,  # https 사용
)


# 파일 저장 기본 설정을 Cloudinary로 설정 (선택 사항)
# Django의 ImageField, FileField에서 저장하는 모든 업로드 파일은 MEDIA_ROOT가 아닌 Cloudinary에 저장됩니다.
# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# # 기본 이미지 url 설정
# BASE_STATIC_URL = STATIC_URL + "images/"
# # 기본 프로필 이미지 url 설정
# DEFAULT_PROFILE_URL = BASE_STATIC_URL + "default_profile.webp"
# DEFAULT_PROFILE_THUMBNAIL_URL = BASE_STATIC_URL + "default_profile_thumb.webp"
# # 기본 게시글 이미지 url 설정
# DEFAULT_POST_URL = BASE_STATIC_URL + "default_post.webp"
# DEFAULT_POST_THUMBNAIL_URL = BASE_STATIC_URL + "default_post_thumb.webp"
# # 기본 이미지 url 설정
# DEFAULT_THUMBNAIL_URL = BASE_STATIC_URL + "default_thumb.webp"  # 예외 대비


# Email
# from django.core.mail.backends.smtp import EmailBackend
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # 개발/테스트용
EMAIL_HOST = "smtp.naver.com"  # 네이버 환결설정에서 볼 수 있음.
EMAIL_USE_TLS = True  # 보안연결
EMAIL_PORT = 587  # 네이버 메일 환경설정에서 확인 가능
EMAIL_HOST_USER = ENV.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = ENV.get("EMAIL_HOST_PASSWORD", "")


# OAuth
NAVER_CLIENT_ID = ENV.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = ENV.get("NAVER_CLIENT_SECRET", "")

KAKAO_REST_API_KEY = ENV.get("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = ENV.get("KAKAO_CLIENT_SECRET", "")

GOOGLE_CLIENT_ID = ENV.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = ENV.get("GOOGLE_CLIENT_SECRET", "")
