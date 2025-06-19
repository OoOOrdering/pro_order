import os
import random
from datetime import timedelta

import cloudinary

from .base import BASE_DIR, ENV, LOGGING

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# 테스트 환경 체크
TESTING = os.environ.get("DJANGO_TESTING") == "True"

# 테스트 환경을 위한 캐시 설정
if TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
            "OPTIONS": {"IGNORE_EXCEPTIONS": True},
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": ENV.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "RETRY_ON_TIMEOUT": True,
                "MAX_CONNECTIONS": 100,
                "CONNECTION_POOL_KWARGS": {
                    "retry_on_timeout": True,
                    "socket_connect_timeout": 5,
                    "socket_timeout": 5,
                },
                "SOCKET_TIMEOUT": 5,
                "SOCKET_CONNECT_TIMEOUT": 5,
                "RETRY_TIMES": 3,
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]

# Logging
LOGGING["handlers"]["console"]["level"] = "DEBUG"
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"

# 시크릿 키를 ENV 변수에 저장된 딕셔너리에서 가져옵니다. 만약 파일에서 읽어온 시크릿 키가 존재하지 않는다면 50자리의 무작위 문자열을 반환합니다.
SECRET_KEY: str = ENV.get(
    "DJANGO_SECRET_KEY",
    "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()?", k=50)),
)

cloudinary.config(
    cloud_name=ENV.get("CLOUD_NAME", "db"),
    api_key=ENV.get("API_KEY", "db"),
    api_secret=ENV.get("API_SECRET", "db"),
    secure=True,  # https 사용
)

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Email
EMAIL_HOST = "smtp.naver.com"  # 네이버 환결설정에서 볼 수 있음.
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ENV.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = ENV.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# OAuth
NAVER_CLIENT_ID = ENV.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = ENV.get("NAVER_CLIENT_SECRET", "")

KAKAO_REST_API_KEY = ENV.get("KAKAO_REST_API_KEY", "")
KAKAO_CLIENT_SECRET = ENV.get("KAKAO_CLIENT_SECRET", "")

GOOGLE_CLIENT_ID = ENV.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = ENV.get("GOOGLE_CLIENT_SECRET", "")

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT 설정
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1),  # access 토큰 만료 1분
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),  # refresh 토큰 만료 1일
    "ROTATE_REFRESH_TOKENS": False,  # refresh 토큰 재발급 여부
    "BLACKLIST_AFTER_ROTATION": False,  # 재발급 시 이전 refresh 토큰 블랙리스트 등록
    "UPDATE_LAST_LOGIN": True,  # 로그인 시 last_login 업데이트
    "ALGORITHM": "HS256",  # 해싱 알고리즘
    "SIGNING_KEY": SECRET_KEY,  # 비밀키
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_NAME": "refresh_token",
}


# swagger
SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "config.urls.swagger_info.swagger_info",
    "USE_SESSION_AUTH": True,
    "JSON_EDITOR": True,
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
        "Token": {"type": "apiKey", "name": "Authorization", "in": "header"},
    },
    "OPERATIONS_SORTER": "alpha",
    "SPEC_URL": "/swagger.json",
}

CORS_ORIGIN_WHITELIST = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS = True

# Cloudinary 설정
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": ENV.get("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": ENV.get("CLOUDINARY_API_KEY"),
    "API_SECRET": ENV.get("CLOUDINARY_API_SECRET"),
}

# 로깅 설정
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# Celery
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# django-debug-toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
