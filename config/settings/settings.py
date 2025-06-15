# config/settings/settings.py

from .base import *  # noqa: F403

# "local", "prod" 중 하나가 환경변수로 주어짐
env = ENV.get("DJANGO_ENV", "local")
if env == "prod":
    from .prod import *  # noqa: F403
else:
    from .local import *  # noqa: F403
