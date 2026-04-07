# AgriGenie Buyer Popup Window Feature - Complete Implementation Guide

## Overview
The buyer popup window feature enables real-time message notifications that appear automatically whenever a buyer receives a message from a farmer, regardless of which page the buyer is viewing. This matches the farmer's experience.

## Architecture

### 1. **Backend (Django)**

#### Database Models (`chat/models.py`)
```python
ChatRoom:
  - farmer: ForeignKey(CustomUser)
  - buyer: ForeignKey(CustomUser)
  - crop: ForeignKey(Crop, optional)
  - is_active: Boolean
  
ChatMessage:
  - room: ForeignKey(ChatRoom)
  - sender: ForeignKey(CustomUser)
  - content: TextField
  - is_read: Boolean (default=False)
  - created_at: DateTime
```

#### API Endpoints (`chat/views.py`)

**1. Get Unread Conversations** - `/chat/api/unread-conversations/`
```python
@login_required
@require_GET
def get_unread_conversations(request):
    """
    Returns up to 3 most recent unread conversations
    Works for both farmers and buyers
    """
    # Query: Find all ChatRooms where user is farmer OR buyer
    ChatRoom.objects.filter(Q(farmer=user) | Q(buyer=user), is_active=True)
    
    # Filter: Get rooms with unread messages NOT from user
    unread_messages = room.messages.filter(is_read=False).exclude(sender=user)
    
    # Response:
    {
        'success': True,
        'conversations': [
            {
                'room_id': 123,
                'room_name': 'Farmer Name',
                'other_user_username': 'farmer_user',
                'other_user_role': 'farmer',
                'last_message': 'Message preview...',
                'unread_count': 2,
                'timestamp': '2026-04-07T10:30:00'
            }
        ],
        'current_user_id': 456
    }
```

**2. Get Conversation History** - `/chat/api/conversation/<room_id>/`
```python
@login_required
def get_conversation_history(request, room_id):
    """
    Returns full conversation for displaying in popup
    """
    # Response:
    {
        'success': True,
        'messages': [
            {
                'id': 1,
                'sender_username': 'farmer_user',
                'content': 'Hello buyer!',
                'timestamp': '2026-04-07T10:00:00',
                'is_read': True
            }
        ]
    }
```

**3. Send Message** - `/chat/api/send/<room_id>/`
```python
@login_required
@require_POST
def send_message_ajax(request, room_id):
    """
    Allows buyers AND farmers to send messages
    No @farmer_approval_required decorator
    """
    # Creates ChatMessage with sender=request.user, is_read=False
    # Returns the created message data
```

**4. Mark as Read** - `/chat/api/mark-read/<room_id>/`
```python
@login_required
@require_POST
def mark_conversation_read(request, room_id):
    """
    Marks messages as read when buyer opens popup
    """
    # Sets is_read=True for all messages in room from others
```

### 2. **Frontend (JavaScript in base.html)**

#### Initialization
```javascript
// Runs only for authenticated users
{% if user.is_authenticated %}
    <script>
        // Initialize chat system on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeChatSystem);
        } else {
            initializeChatSystem();
        }
    </script>
{% endif %}
```

#### Core Functions

**A. Initialize System** - `initializeChatSystem()`
```javascript
function initializeChatSystem() {
    checkUnreadMessages();           // Update badge count
    fetchAndDisplayChatPopups();     // Check for new popups
    
    // Poll every 1.5 seconds for new conversations
    setInterval(() => {
        checkUnreadMessages();
        fetchAndDisplayChatPopups();
    }, 1500);
}
```

**B. Fetch and Display** - `fetchAndDisplayChatPopups()`
```javascript
function fetchAndDisplayChatPopups() {
    fetch('/chat/api/unread-conversations/')
        .then(r => r.json())
        .then(data => {
            // data.conversations = array of unread conversations
            for (const conversation of data.conversations) {
                if (!alreadyDisplayed(conversation.room_id)) {
                    // Create and display popup
                    displayChatPopup(conversation);
                    rememberAsDisplayed(conversation.room_id);
                }
            }
        });
}
```

**C. Display Popup** - `displayChatPopup(conversation)`
```javascript
function displayChatPopup(conversation) {
    // Create popup div with id=chat-popup-{room_id}
    popup.innerHTML = `
        <div class="chat-popup-window offset-N" data-room-id="${room_id}">
            <div class="chat-popup-header">
                <span>${other_user_name}</span>
                <button onclick="closePopup(${room_id})">×</button>
            </div>
            <div class="chat-popup-messages"></div>
            <div class="chat-popup-input">
                <input type="text" placeholder="Type message...">
                <button onclick="sendPopupMessage(${room_id})">Send</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // Load conversation history
    loadChatPopupConversation(room_id);
    
    // Start polling for new messages every 1 second
    startPopupMessageRefresh(room_id);
}
```

**D. Load Conversation** - `loadChatPopupConversation(room_id)`
```javascript
function loadChatPopupConversation(room_id) {
    fetch(`/chat/api/conversation/${room_id}/`)
        .then(r => r.json())
        .then(data => {
            // Display all messages from data.messages
            // Scroll to bottom
            // Mark as read via POST /chat/api/mark-read/{room_id}/
        });
}
```

**E. Real-time Refresh** - `startPopupMessageRefresh(room_id)`
```javascript
function startPopupMessageRefresh(room_id) {
    // Poll every 1 second for new messages in this specific popup
    const interval = setInterval(() => {
        fetch(`/chat/api/messages/${room_id}/?last_id=...`)
            .then(r => r.json())
            .then(data => {
                // Append new messages to popup
                // Update is_read status
            });
    }, 1000);
    
    popupRefreshIntervals[room_id] = interval;
}
```

**F. Send Message** - `sendPopupMessage(room_id)`
```javascript
function sendPopupMessage(room_id) {
    const message = getInputValue(room_id);
    
    fetch(`/chat/api/send/${room_id}/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(r => r.json())
    .then(data => {
        // Add message to popup display
        // Clear input field
        // Scroll to bottom
    });
}
```

### 3. **Frontend (CSS in base.html)**

```css
.chat-popup-window {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 400px;
    height: 550px;
    border-radius: 12px;
    box-shadow: 0 5px 40px rgba(0,0,0,0.16);
    background: white;
    display: flex;
    flex-direction: column;
    z-index: 9999;
    animation: slideIn 0.3s ease-out;
}

/* Stack up to 3 popups */
.chat-popup-window.offset-1 { right: 20px; }
.chat-popup-window.offset-2 { right: 430px; }
.chat-popup-window.offset-3 { right: 860px; }
```

## Data Flow Diagram

```
1. FARMER sends message to BUYER
   ├─ Farmer accesses start_chat view (@ farmer_approval_required)
   ├─ ChatRoom created: farmer=Farmer, buyer=Buyer
   ├─ Farmer sends message via send_message_ajax
   └─ ChatMessage created: sender=Farmer, is_read=False

2. BUYER's browser polls (every 1.5 seconds)
   ├─ fetch(/chat/api/unread-conversations/)
   ├─ Backend query: ChatRoom.filter(Q(farmer=Buyer) | Q(buyer=Buyer))
   ├─ Filter: messages.filter(is_read=False).exclude(sender=Buyer)
   └─ Returns conversation with Farmer

3. BUYER sees popup
   ├─ JavaScript receives conversation data
   ├─ Creates popup div in DOM
   ├─ Loads full conversation history
   ├─ Starts polling for new messages (every 1 second)
   └─ Marks messages as read

4. BUYER sends reply
   ├─ Buyer types message in popup
   ├─ fetch(POST /chat/api/send/{room_id}/)
   ├─ ChatMessage created: sender=Buyer, is_read=False
   ├─ Message appears in popup immediately
   └─ Farmer's browser will see popup on next poll cycle

5. FARMER sees popup (same as step 2-3)
```

## Testing the Feature

### Quick Test
```bash
# 1. Start Django server
python manage.py runserver

# 2. Open two browser windows/tabs
# Tab 1: Log in as FARMER
# Tab 2: Log in as BUYER

# 3. Farmer sends message to Buyer
# Tab 1: Go to marketplace, view crop, click "Message"
#        This starts a chat with buyer
#        Type and send a message

# 4. Buyer sees popup
# Tab 2: Open F12 console, look for [Chat Popup] logs
#        Popup should appear in bottom-right corner
#        Popup shows full conversation history
#        Popup auto-closes or can be closed manually

# 5. Buyer replies
# Tab 2: Type reply in popup, click Send
#        Message appears immediately

# 6. Farmer sees popup  
# Tab 1: Check for popup on any page
#        Should appear automatically
```

### Database Test
```python
# In Django shell: python manage.py shell
from chat.models import ChatRoom, ChatMessage
from users.models import CustomUser

# Get test users
farmer = CustomUser.objects.get(username='farmer_username')
buyer = CustomUser.objects.get(username='buyer_username')

# Check ChatRoom
room = ChatRoom.objects.filter(farmer=farmer, buyer=buyer).first()
print(f"Room exists: {room is not None}")

# Check unread messages
unread = room.messages.filter(is_read=False).exclude(sender=buyer)
print(f"Unread messages for buyer: {unread.count()}")

# Manually test the query
rooms = ChatRoom.objects.filter(
    Q(farmer=buyer) | Q(buyer=buyer),
    is_active=True
).prefetch_related('messages')
print(f"Rooms found for buyer: {rooms.count()}")

for r in rooms:
    unread = r.messages.filter(is_read=False).exclude(sender=buyer)
    if unread.exists():
        print(f"  Room {r.id}: {unread.count()} unread messages")
```

## Troubleshooting

### Issue: Buyer doesn't see popup
**Debug Steps:**
1. Check browser console (F12)
   - Look for `[Chat Popup]` logs
   - Should see "Fetching unread conversations..."
   - Check API response for errors

2. Check Network tab (F12)
   - Verify `/chat/api/unread-conversations/` request succeeds (200 OK)
   - Check response body - should have `conversations` array

3. Check Django server logs
   - Should see `[DEBUG] get_unread_conversations START for user: {username}`
   - Should show room count and unread message count

4. Check database
   - Verify ChatRoom exists with this buyer
   - Verify messages exist and is_read=False
   - Verify sender is NOT the buyer

### Issue: Popup appears but doesn't show messages
**Solutions:**
- Check `/chat/api/conversation/{room_id}/` endpoint
- Verify loadChatPopupConversation() function is called
- Check JavaScript console for errors

### Issue: Messages don't update in real-time
**Solutions:**
- Verify startPopupMessageRefresh() is called
- Check `/chat/api/messages/{room_id}/` endpoint
- Verify polling interval is set (should be 1000ms)

## Files Modified/Created

```
Modified:
  - chat/views.py          : Added/updated API endpoints
  - templates/base.html    : Added popup JS and CSS
  - chat/urls.py           : Added API routes
  
Created:
  - test_buyer_popup.py    : Test script to verify functionality
  - BUYER_POPUP_VERIFICATION.md : Verification checklist
```

## Key Implementation Notes

1. **Both Farmer and Buyer can:**
   - Send messages (send_message_ajax has @login_required only)
   - Receive messages (get_unread_conversations works for both)
   - See popups (JavaScript runs for all authenticated users)

2. **Only Farmers can:**
   - Initiate chats (start_chat has @farmer_approval_required)
   - But this is OK - chat room is created when farmer messages buyer

3. **Polling Intervals:**
   - Each browser tab polls for NEW CONVERSATIONS every 1.5 seconds
   - Each OPEN POPUP polls for NEW MESSAGES every 1 second
   - Balance between responsiveness and server load

4. **Display Limits:**
   - Maximum 3 popups shown at once
   - Top 3 most recent unread conversations
   - Older notifications can be accessed from Messages page

5. **Security:**
   - All endpoints require @login_required
   - Users can only see their own conversations
   - Cannot access other users' popups or messages

## Success Criteria

✅ When you log in as a buyer and:
- [ ] Receive a message from farmer
- Popup appears automatically within 1-2 seconds
- [ ] Popup shows farmer's name and message
- [ ] Full conversation history is visible
- [ ] You can type and send a reply
- [ ] Reply appears immediately
- [ ] Farmer sees popup with your reply
- [ ] No JavaScript errors in console
- [ ] Works on any page (not just /chat/)
