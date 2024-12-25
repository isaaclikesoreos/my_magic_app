"""
ASGI config for a_core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')

django_asgi_app = get_asgi_application()

from a_rtchat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from a_drafting.routing import websocket_urlpatterns as draft_websocket_urlpatterns

# Combine WebSocket routing patterns
combined_websocket_urlpatterns = chat_websocket_urlpatterns + draft_websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(combined_websocket_urlpatterns))
    ),


})
