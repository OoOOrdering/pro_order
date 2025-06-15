# ruff: noqa: F405

import random

from dotenv import load_dotenv

from .base import *  # noqa: F403

load_dotenv(BASE_DIR / "envs/.env.prod")  # 환경 변수 파일 로드

# DEBUG = True
# ALLOWED_HOSTS: list[str] = []

DEBUG = False
ALLOWED_HOSTS: list[str] = [
    "127.0.0.1",
    "localhost",
    "3.39.10.22",  # EC2 퍼블릭 IP
]

# 시크릿 키를 ENV 변수에 저장된 딕셔너리에서 가져옵니다. 만약 파일에서 읽어온 시크릿 키가 존재하지 않는다면 50자리의 무작위 문자열을 반환합니다.
SECRET_KEY: str = os.getenv(
    "DJANGO_SECRET_KEY",
    "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()?", k=50)),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "NAME": os.getenv("POSTGRES_DB", "oz_collabo"),
        "PORT": os.getenv("POSTGRES_PORT", 5432),
    }
}


# Email
# from django.core.mail.backends.smtp import EmailBackend
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.naver.com"  # 네이버 환결설정에서 볼 수 있음.
EMAIL_USE_TLS = True  # 보안연결
EMAIL_PORT = 587  # 네이버 메일 환경설정에서 확인 가능
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")


# OAuth
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
