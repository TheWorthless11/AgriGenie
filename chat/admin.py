from django.contrib import admin
from .models import ChatRoom, ChatMessage


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """Admin interface for ChatRoom model"""
    list_display = ('id', 'farmer', 'buyer', 'crop', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('farmer__username', 'buyer__username', 'crop__master_crop__crop_name')
    raw_id_fields = ('farmer', 'buyer', 'crop')
    date_hierarchy = 'created_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model"""
    list_display = ('id', 'room', 'sender', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'content')
    raw_id_fields = ('room', 'sender')
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        """Show truncated message content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
