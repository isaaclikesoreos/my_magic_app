from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from .consumers import DraftConsumer

websocket_urlpatterns = [
    path("ws/drafts/<int:draft_id>/", DraftConsumer.as_asgi()),  # Match the frontend URL
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
