# config/settings/settings.py

from .base import *  # noqa: F403

# "local", "prod" 중 하나가 환경변수로 주어짐
env = ENV.get("DJANGO_ENV", "local")
if env == "prod":
    from .prod import *  # noqa: F403
else:
    from .local import *  # noqa: F403

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": ["redis://3.34.108.96:6379/1"],
        },
    },
}
