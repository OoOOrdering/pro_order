from .base import ENV, LOGGING

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ENV.get("DJANGO_ALLOWED_HOSTS", "").split(",")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": ENV.get("DB_NAME", "pr_order"),
        "USER": ENV.get("DB_USER", "postgres"),
        "PASSWORD": ENV.get("DB_PASSWORD", ""),
        "HOST": ENV.get("DB_HOST", "localhost"),
        "PORT": ENV.get("DB_PORT", "5432"),
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS settings
CORS_ALLOWED_ORIGINS = ENV.get("CORS_ALLOWED_ORIGINS", "").split(",")

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = ENV.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(ENV.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ENV.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = ENV.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = ENV.get("DEFAULT_FROM_EMAIL", "")

# Cloudinary settings
CLOUDINARY = {
    "cloud_name": ENV.get("CLOUDINARY_CLOUD_NAME", ""),
    "api_key": ENV.get("CLOUDINARY_API_KEY", ""),
    "api_secret": ENV.get("CLOUDINARY_API_SECRET", ""),
}

# Logging
LOGGING["handlers"]["console"]["level"] = "WARNING"
LOGGING["loggers"]["django"]["level"] = "WARNING"
LOGGING["loggers"]["apps"]["level"] = "WARNING"
