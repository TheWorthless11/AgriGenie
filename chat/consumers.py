"""
WebSocket consumers for real-time chat functionality.
Handles connection, disconnection, and message broadcasting.
"""

import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat between farmer and buyer.
    Uses Redis channel layer for message broadcasting.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user is part of this chat room
        is_member = await self.is_room_member()
        if not is_member:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify room that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.user.username,
                'user_id': self.user.id,
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Notify room that user left
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.user.username,
                    'user_id': self.user.id,
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                message = data.get('message', '').strip()
                if message:
                    # Save message to database
                    saved_message = await self.save_message(message)
                    
                    # Broadcast message to room
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'sender_id': self.user.id,
                            'sender_username': self.user.username,
                            'message_id': saved_message['id'],
                            'timestamp': saved_message['timestamp'],
                        }
                    )
            
            elif message_type == 'typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'username': self.user.username,
                        'user_id': self.user.id,
                        'is_typing': data.get('is_typing', False),
                    }
                )
            
            elif message_type == 'mark_read':
                # Mark messages as read
                await self.mark_messages_read()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'messages_read',
                        'reader_id': self.user.id,
                    }
                )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_join(self, event):
        """Send user join notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'username': event['username'],
            'user_id': event['user_id'],
        }))
    
    async def user_leave(self, event):
        """Send user leave notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'username': event['username'],
            'user_id': event['user_id'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
    
    async def messages_read(self, event):
        """Send messages read notification"""
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'reader_id': event['reader_id'],
        }))
    
    @database_sync_to_async
    def is_room_member(self):
        """Check if user is a member of the chat room"""
        from chat.models import ChatRoom
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return self.user == room.farmer or self.user == room.buyer
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        from chat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        # Update room's updated_at timestamp
        room.save()
        return {
            'id': message.id,
            'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @database_sync_to_async
    def mark_messages_read(self):
        """Mark all unread messages in room as read for current user"""
        from chat.models import ChatRoom, ChatMessage
        room = ChatRoom.objects.get(id=self.room_id)
        # Mark messages sent by the other user as read
        ChatMessage.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)
