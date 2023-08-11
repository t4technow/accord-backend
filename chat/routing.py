from django.urls import path
from .consumers import (
    ChatConsumer,
    NotificationConsumer,
    OnlineStatusConsumer,
    PeerConnectionConsumer,
)

websocket_urlpatterns = [
    path("chat/", ChatConsumer.as_asgi()),
    path("notifications/", NotificationConsumer.as_asgi()),
    path("online-status/", OnlineStatusConsumer.as_asgi()),
    path("peersocket/", PeerConnectionConsumer.as_asgi()),
]
