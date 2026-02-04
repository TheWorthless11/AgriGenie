"""
Chat models for real-time messaging between farmers and buyers.
Supports one-on-one chat rooms and persistent message storage.
"""

from django.db import models
from users.models import CustomUser
from farmer.models import Crop


class ChatRoom(models.Model):
    """
    A chat room between two users (farmer and buyer).
    Can optionally be linked to a specific crop/product.
    """
    farmer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='farmer_chat_rooms'
    )
    buyer = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='buyer_chat_rooms'
    )
    crop = models.ForeignKey(
        Crop, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='chat_rooms',
        help_text="Optional: Link chat to a specific crop listing"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['farmer', 'buyer', 'crop']
    
    def __str__(self):
        crop_info = f" about {self.crop.master_crop.crop_name}" if self.crop else ""
        return f"Chat: {self.farmer.username} & {self.buyer.username}{crop_info}"
    
    @property
    def room_name(self):
        """Generate unique room name for WebSocket"""
        return f"chat_{self.id}"
    
    def get_other_user(self, current_user):
        """Get the other participant in the chat"""
        if current_user == self.farmer:
            return self.buyer
        return self.farmer


class ChatMessage(models.Model):
    """
    Individual messages within a chat room.
    Stores message content, sender, and read status.
    """
    room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='chat_messages_sent'
    )
    content = models.TextField()
    image = models.ImageField(
        upload_to='chat_images/', 
        null=True, 
        blank=True,
        help_text="Optional image attachment"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}..."
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
