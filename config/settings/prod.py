import random

from config.settings.base import ENV

# DEBUG = True
DEBUG = False
ALLOWED_HOSTS: list[str] = [
    "127.0.0.1",
    "localhost",
    "43.203.181.6",
    "wistar.n-e.kr",
]  # EC2 퍼블릭 IP

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

# S3 사용시 설정
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": ENV.get("S3_ACCESS_KEY", ""),
            "secret_key": ENV.get("S3_SECRET_ACCESS_KEY", ""),
            "bucket_name": ENV.get("S3_STORAGE_BUCKET_NAME", ""),
            "region_name": ENV.get("S3_REGION_NAME", ""),
            "custom_domain": f'{ENV.get("S3_STORAGE_BUCKET_NAME", "")}.s3.amazonaws.com',
            "location": "media",
            "default_acl": "public-read",
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": ENV.get("S3_ACCESS_KEY", ""),
            "secret_key": ENV.get("S3_SECRET_ACCESS_KEY", ""),
            "bucket_name": ENV.get("S3_STORAGE_BUCKET_NAME", ""),
            "region_name": ENV.get("S3_REGION_NAME", ""),
            "custom_domain": f'{ENV.get("S3_STORAGE_BUCKET_NAME", "")}.s3.amazonaws.com',
            "location": "static",
            "default_acl": "public-read",
        },
    },
}

# # custom_domain이 설정되어 있으면, 이 도메인을 사용해서 URL을 생성
# # 그렇지 않으면 기본 Amazon S3 URL (s3.{region}.amazonaws.com/{bucket}/...)을 사용

# Static, Media URL 수정
MEDIA_URL = f"https://{ENV.get('S3_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/media/"
STATIC_URL = f"https://{ENV.get('S3_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/static/"


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
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
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
