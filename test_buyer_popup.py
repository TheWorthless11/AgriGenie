"""
Test script to verify buyer popup system works correctly.
Run with: python manage.py shell < test_buyer_popup.py
"""

from django.db.models import Q
from users.models import CustomUser
from chat.models import ChatRoom, ChatMessage

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

print(f"\n{BLUE}{'='*80}")
print("TEST: Buyer Popup System Verification")
print(f"{'='*80}{RESET}\n")

# Find test accounts
print(f"{YELLOW}[STEP 1] Finding test users...{RESET}")
farmers = CustomUser.objects.filter(role='farmer')
buyers = CustomUser.objects.filter(role='buyer')

print(f"  Found {farmers.count()} farmers")
print(f"  Found {buyers.count()} buyers")

if farmers.count() == 0 or buyers.count() == 0:
    print(f"{RED}❌ Not enough users for testing. Need at least 1 farmer and 1 buyer.{RESET}\n")
    exit(1)

farmer = farmers.first()
buyer = buyers.first()

print(f"  Using farmer: {GREEN}{farmer.username}{RESET}")
print(f"  Using buyer: {GREEN}{buyer.username}{RESET}\n")

# Check for existing chat rooms
print(f"{YELLOW}[STEP 2] Checking existing chat rooms...{RESET}")
rooms = ChatRoom.objects.filter(
    Q(farmer=farmer) | Q(buyer=farmer),
    is_active=True
)
print(f"  Farmer has {GREEN}{rooms.count()}{RESET} active chat rooms\n")

rooms = ChatRoom.objects.filter(
    Q(farmer=buyer) | Q(buyer=buyer),
    is_active=True
)
print(f"  Buyer has {GREEN}{rooms.count()}{RESET} active chat rooms\n")

# Test creating a chat room (simulating farmer initiating)
print(f"{YELLOW}[STEP 3] Creating test chat room (farmer→buyer)...{RESET}")
room, created = ChatRoom.objects.get_or_create(
    farmer=farmer,
    buyer=buyer,
    crop=None,
    defaults={'is_active': True}
)

if created:
    print(f"  {GREEN}✓ Created new room{RESET}")
else:
    print(f"  {YELLOW}✓ Using existing room{RESET}")

print(f"  Room ID: {BLUE}{room.id}{RESET}\n")

# Test creating a message
print(f"{YELLOW}[STEP 4] Creating test message (farmer→buyer)...{RESET}")
message = ChatMessage.objects.create(
    room=room,
    sender=farmer,
    content="Test message from farmer to buyer"
)
print(f"  {GREEN}✓ Created message ID {message.id}{RESET}")
print(f"  Sender: {farmer.username}")
print(f"  Content: {message.content}")
print(f"  Is Read: {message.is_read}")
print(f"  Timestamp: {message.created_at}\n")

# Test BUYER's unread conversations query
print(f"{YELLOW}[STEP 5] Testing buyer's unread conversations query...{RESET}")
recent_conversations = ChatRoom.objects.filter(
    Q(farmer=buyer) | Q(buyer=buyer),
    is_active=True
).prefetch_related('messages').distinct()

print(f"  Buyer found {GREEN}{recent_conversations.count()}{RESET} active chat rooms")

rooms_with_unread = []
for room in recent_conversations:
    unread_from_others = room.messages.filter(
        is_read=False
    ).exclude(
        sender=buyer
    ).order_by('-created_at')
    
    print(f"\n  Room {room.id}:")
    print(f"    - Farmer: {room.farmer.username}")
    print(f"    - Buyer: {room.buyer.username}")
    print(f"    - Total messages: {room.messages.count()}")
    print(f"    - Unread from others: {GREEN}{unread_from_others.count()}{RESET}")
    
    if unread_from_others.exists():
        rooms_with_unread.append((room, unread_from_others.first()))
        print(f"    - {GREEN}✓ HAS UNREAD MESSAGES{RESET}")
        for msg in unread_from_others:
            print(f"      - From: {msg.sender.username}, Content: {msg.content[:50]}")
    else:
        print(f"    - {RED}✗ No unread messages{RESET}")

print(f"\n{YELLOW}[STEP 6] Processing unread conversations for popup...{RESET}")
rooms_with_unread.sort(key=lambda x: x[1].created_at, reverse=True)
top_3 = rooms_with_unread[:3]

print(f"  Total rooms with unread: {GREEN}{len(rooms_with_unread)}{RESET}")
print(f"  Top 3 for popup: {GREEN}{len(top_3)}{RESET}\n")

conversations = []
for room, last_unread in top_3:
    other_user = room.get_other_user(buyer)
    unread_count = room.messages.filter(is_read=False).exclude(sender=buyer).count()
    
    conversation_data = {
        'room_id': room.id,
        'room_name': f"{other_user.get_full_name() or other_user.username}",
        'other_user_id': other_user.id,
        'other_user_username': other_user.username,
        'other_user_role': other_user.role,
        'last_message': last_unread.content[:100],
        'last_message_id': last_unread.id,
        'sender_username': last_unread.sender.username,
        'unread_count': unread_count,
        'timestamp': last_unread.created_at.isoformat(),
    }
    conversations.append(conversation_data)
    
    print(f"  {GREEN}✓ Conversation {room.id}:{RESET}")
    print(f"    - Room Name: {conversation_data['room_name']}")
    print(f"    - Other User: {conversation_data['other_user_username']} ({conversation_data['other_user_role']})")
    print(f"    - Last Message: {conversation_data['last_message']}")
    print(f"    - Unread Count: {conversation_data['unread_count']}")
    print(f"    - Timestamp: {conversation_data['timestamp']}\n")

# Final result
print(f"{YELLOW}[RESULT]{RESET}")
if conversations:
    print(f"{GREEN}✓ SUCCESS!{RESET} Buyer would receive {GREEN}{len(conversations)}{RESET} popup(s)")
    print(f"\nPopup data that would be sent to browser:")
    print(f"{BLUE}{conversations}{RESET}")
else:
    print(f"{RED}✗ FAILURE!{RESET} No conversations returned for buyer popup")
    print(f"\nPossible causes:")
    print(f"  1. No ChatRoom exists between farmer and buyer")
    print(f"  2. ChatRoom exists but buyer is not in it")
    print(f"  3. Messages exist but are already marked as read")
    print(f"  4. Messages are from the buyer themselves (filtered out)")

print(f"\n{BLUE}{'='*80}{RESET}\n")
