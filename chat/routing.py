"""
WebSocket URL routing for chat application.
Maps WebSocket URLs to their respective consumers.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket URL for chat rooms
    # Example: ws://localhost:8000/ws/chat/1/
    re_path(r'ws/chat/(?P<room_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
