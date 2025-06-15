from ..settings.base import ENV

# "local", "prod" 중 하나가 환경변수로 주어짐
# env = ENV.get("DJANGO_ENV", "local")
env = "local"

if env == "prod":
    from .urls_prod import *  # noqa: F403
else:
    from .urls_dev import *  # noqa: F403
