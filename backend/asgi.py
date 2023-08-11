import os
import django

django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.middlewares import JwtAuthForAsgiStack

from chat.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            JwtAuthForAsgiStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
