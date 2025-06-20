from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import apps.chat_message.routing
import apps.notification.routing
import apps.order.routing

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(
                apps.chat_message.routing.websocket_urlpatterns
                + apps.notification.routing.websocket_urlpatterns
                + apps.order.routing.websocket_urlpatterns
            )
        ),
    }
)
