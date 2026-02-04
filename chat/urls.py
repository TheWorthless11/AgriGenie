"""
URL patterns for chat application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Chat list - shows all conversations
    path('', views.chat_list, name='chat_list'),
    
    # Individual chat room
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    
    # Start new chat with a user (optionally about a crop)
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
    path('start/<int:user_id>/crop/<int:crop_id>/', views.start_chat, name='start_chat_with_crop'),
    
    # Delete chat room
    path('delete/<int:room_id>/', views.delete_chat, name='delete_chat'),
    
    # API: Get unread message count
    path('api/unread/', views.get_unread_count, name='chat_unread_count'),
    
    # API: Send message (AJAX fallback)
    path('api/send/<int:room_id>/', views.send_message_ajax, name='send_message_ajax'),
    
    # API: Get messages (polling fallback)
    path('api/messages/<int:room_id>/', views.get_messages_ajax, name='get_messages_ajax'),
]
