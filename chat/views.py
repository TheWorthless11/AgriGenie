"""
Chat views for handling chat room creation, listing, and rendering.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max, Count
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
import json
from .models import ChatRoom, ChatMessage
from farmer.models import Crop
from farmer.decorators import farmer_approval_required
from users.models import CustomUser


@login_required
@farmer_approval_required('marketplace')
def chat_list(request):
    """
    Display list of all chat rooms for the current user.
    Shows farmer chats for farmers, buyer chats for buyers.
    Farmers must be approved to access chat.
    """
    user = request.user
    
    # Get all chat rooms where user is participant
    chat_rooms = ChatRoom.objects.filter(
        Q(farmer=user) | Q(buyer=user),
        is_active=True
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count(
            'messages',
            filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
        )
    ).order_by('-last_message_time')
    
    # Add other user info to each room
    rooms_with_info = []
    for room in chat_rooms:
        other_user = room.get_other_user(user)
        last_message = room.messages.last()
        rooms_with_info.append({
            'room': room,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': room.unread_count,
        })
    
    context = {
        'chat_rooms': rooms_with_info,
        'total_unread': sum(r['unread_count'] for r in rooms_with_info),
    }
    
    return render(request, 'chat/chat_list.html', context)


@login_required
@farmer_approval_required('marketplace')
def chat_room(request, room_id):
    """
    Display individual chat room with message history.
    Farmers must be approved to access chat.
    """
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verify user is a participant
    if user != room.farmer and user != room.buyer:
        messages.error(request, 'You do not have access to this chat.')
        return redirect('chat_list')
    
    # Get other user
    other_user = room.get_other_user(user)
    
    # Get message history
    chat_messages = room.messages.select_related('sender').order_by('created_at')
    
    # Mark unread messages as read
    room.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
    
    context = {
        'room': room,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'crop': room.crop,
    }
    
    return render(request, 'chat/chat_room.html', context)


@login_required
@farmer_approval_required('marketplace')
def start_chat(request, user_id, crop_id=None):
    """
    Start a new chat or open existing chat with another user.
    Optionally link to a specific crop.
    Farmers must be approved to send messages.
    """
    current_user = request.user
    other_user = get_object_or_404(CustomUser, id=user_id)
    
    # Prevent chatting with self
    if current_user == other_user:
        messages.error(request, 'You cannot chat with yourself.')
        return redirect('chat_list')
    
    # Determine farmer and buyer
    if current_user.role == 'farmer':
        farmer = current_user
        buyer = other_user
    else:
        farmer = other_user
        buyer = current_user
    
    # Get crop if provided
    crop = None
    if crop_id:
        crop = get_object_or_404(Crop, id=crop_id)
    
    # Find existing chat room or create new one
    room, created = ChatRoom.objects.get_or_create(
        farmer=farmer,
        buyer=buyer,
        crop=crop,
        defaults={'is_active': True}
    )
    
    if created:
        messages.success(request, f'Started new chat with {other_user.username}')
    
    return redirect('chat_room', room_id=room.id)


@login_required
def get_unread_count(request):
    """
    API endpoint to get unread message count for notifications.
    """
    user = request.user
    unread_count = ChatMessage.objects.filter(
        room__in=ChatRoom.objects.filter(
            Q(farmer=user) | Q(buyer=user),
            is_active=True
        ),
        is_read=False
    ).exclude(sender=user).count()
    
    return JsonResponse({'unread_count': unread_count})


@login_required
def delete_chat(request, room_id):
    """
    Soft delete (deactivate) a chat room.
    """
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, id=room_id)
        user = request.user
        
        # Verify user is a participant
        if user != room.farmer and user != room.buyer:
            messages.error(request, 'You do not have access to this chat.')
            return redirect('chat_list')
        
        room.is_active = False
        room.save()
        messages.success(request, 'Chat deleted successfully.')
    
    return redirect('chat_list')


@login_required
@farmer_approval_required('marketplace')
@require_POST
def send_message_ajax(request, room_id):
    """
    AJAX endpoint to send a message (fallback when WebSocket not available).
    Farmers must be approved to send messages.
    """
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verify user is a participant
    if user != room.farmer and user != room.buyer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Create the message
        chat_message = ChatMessage.objects.create(
            room=room,
            sender=user,
            content=message_content
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': chat_message.id,
                'content': chat_message.content,
                'sender_id': user.id,
                'sender_username': user.username,
                'timestamp': chat_message.created_at.isoformat(),
                'is_read': chat_message.is_read,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@farmer_approval_required('marketplace')
@require_GET
def get_messages_ajax(request, room_id):
    """
    AJAX endpoint to get messages (polling fallback when WebSocket not available).
    Returns messages after a given message ID or timestamp.
    Farmers must be approved to view messages.
    """
    user = request.user
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Verify user is a participant
    if user != room.farmer and user != room.buyer:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get messages after a certain ID (for polling)
    after_id = request.GET.get('after_id', 0)
    try:
        after_id = int(after_id)
    except ValueError:
        after_id = 0
    
    # Get new messages
    new_messages = room.messages.filter(id__gt=after_id).select_related('sender').order_by('created_at')
    
    # Mark messages from other user as read
    new_messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender.id,
        'sender_username': msg.sender.username,
        'timestamp': msg.created_at.isoformat(),
        'is_read': msg.is_read,
    } for msg in new_messages]
    
    return JsonResponse({
        'messages': messages_data,
        'current_user_id': user.id,
    })
