import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter

from chats.middleware import JWTAuthMiddleware
from chats.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        # HTTP
        "http": django_asgi_app,

        # WebSocket
        "websocket": JWTAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        ),
    }
)