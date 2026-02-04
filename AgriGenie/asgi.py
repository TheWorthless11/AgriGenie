"""
ASGI config for AgriGenie project.

It exposes the ASGI callable as a module-level variable named ``application``.
Supports both HTTP and WebSocket protocols for real-time chat.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriGenie.settings')

# Setup Django FIRST before importing anything else
import django
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Import chat routing after Django setup
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP requests handled by Django ASGI
    "http": django_asgi_app,
    
    # WebSocket requests handled by Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
