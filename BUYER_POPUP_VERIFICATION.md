# Buyer Popup Window - Complete Verification Checklist

## Quick Start Guide

### 1. **Verify Farmer Popup Works (Baseline)**
```
Test: While logged in as FARMER, have a BUYER send you a message
Expected: Popup window appears in bottom-right corner with message
Result: ✓ YES / ✗ NO
```

### 2. **Verify Buyer Can Receive Messages** 
```
Test: While logged in as BUYER, receive a message from a FARMER
Check: Browser Console (F12)
Look for: [Chat Popup] logs showing conversations
Expected: Should see API response with farmer's message
Result: ✓ YES / ✗ NO
```

### 3. **Run Database Test**
```
Command: python manage.py shell < test_buyer_popup.py
Expected: Shows that buyer finds unread conversations
Sections to verify:
  - [STEP 2] Buyer has active chat rooms
  - [STEP 5] Buyer finds unread messages
  - [RESULT] Success message with popup data
```

### 4. **Manual Browser Console Test**

**FOR FARMER:**
1. Log in as Farmer
2. Open F12 → Console
3. Copy and paste this:
```javascript
fetch('/chat/api/unread-conversations/').then(r => r.json()).then(d => console.log('FARMER RESPONSE:', d))
```
4. Look for: array of conversations with `room_id`, `other_user_username`

**FOR BUYER:**
1. Log in as Buyer
2. Open F12 → Console
3. Copy and paste this:
```javascript
fetch('/chat/api/unread-conversations/').then(r => r.json()).then(d => console.log('BUYER RESPONSE:', d))
```
4. Look for: Same format response as farmer

### 5. **Compare Responses**
- Farmer response: `{success: true, conversations: [...]}`
- Buyer response: Should be identical format

If buyer response is empty `conversations: []`:
- Issue is likely in get_unread_conversations query or database

If buyer response has error:
- Issue is likely permission/decorator

## Complete System Verification

### Backend API Endpoints (Django)
- [ ] `/chat/api/unread-conversations/` exists
- [ ] Endpoint has `@login_required` only
- [ ] Endpoint returns JSON with `success`, `conversations`, `current_user_id`
- [ ] Database query: `ChatRoom.objects.filter(Q(farmer=user) | Q(buyer=user))`

### Frontend JavaScript (base.html)
- [ ] Script block inside `{% if user.is_authenticated %}`
- [ ] `initializeChatSystem()` function exists
- [ ] `fetchAndDisplayChatPopups()` function exists
- [ ] Polling interval set to 1500ms
- [ ] Popup CSS styles defined (with `.chat-popup-window` class)

### HTML Elements
- [ ] `<div id="chat-popups-container"></div>` exists in base.html
- [ ] Popup divs created with `class="chat-popup-window"` and `data-room-id`
- [ ] CSS includes animations and positioning

### Database Models
- [ ] `ChatRoom` model: `farmer` and `buyer` ForeignKey fields
- [ ] `ChatMessage` model: `is_read` field defaults to False
- [ ] Messages can be created and retrieved for both roles

## Expected Behavior

### When Farmer Sends Message to Buyer:
```
1. Farmer initiates chat (start_chat view)
2. ChatRoom created: farmer=farmer_user, buyer=buyer_user
3. Message sent via send_message_ajax, is_read=False
4. Buyer's browser polls /chat/api/unread-conversations/
5. Query finds ChatRoom where buyer=buyer_user
6. Finds unread messages where sender≠buyer
7. Returns conversation data to JavaScript
8. JavaScript creates popup window
9. Popup displays in buyer's browser
```

### When Buyer Sends Reply:
```
1. Buyer clicks reply in popup
2. Message sent via send_message_ajax (no decorators block this)
3. Message added to ChatRoom, is_read=False
4. Farmer's browser polls /chat/api/unread-conversations/
5. Farmer sees popup appear
```

## Debugging Steps

### If Buyer Doesn't See Popup:

**Step A: Check Browser Console**
- Open F12, go to Console tab
- Filter for `[Chat` logs
- Check timestamp - is polling happening?
- Check Network tab - are API calls being made?

**Step B: Check Django Server**
- Look for `[DEBUG]` print statements
- Search for buyer's username
- Check if "Found N active chat rooms" shows >0

**Step C: Test API Directly**
```bash
# As farmer user (works)
curl http://localhost:8000/chat/api/unread-conversations/

# As buyer user (should also work)
curl http://localhost:8000/chat/api/unread-conversations/
```

**Step D: Database Check**
```python
# In Django shell
from chat.models import ChatRoom
from users.models import CustomUser

buyer = CustomUser.objects.get(username='buyer_username')
rooms = ChatRoom.objects.filter(buyer=buyer)
print(f"Buyer has {rooms.count()} chat rooms")

for room in rooms:
    unread = room.messages.filter(is_read=False).exclude(sender=buyer)
    print(f"Room {room.id}: {unread.count()} unread")
```

## Common Issues & Solutions

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Buyer never sees any popup | Browser console shows no logs | Check if script block is loading |
| Buyer sees empty conversations | Server logs show 0 rooms | Check ChatRoom creation |
| API returns error | Check network tab | Verify decorator is @login_required |
| Popup creates but is hidden | Check CSS/Z-index | Verify popup styles in base.html |
| Popup appears but doesn't update | Polling logs show freeze | Check JavaScript for errors |

## Success Indicators

✅ **You'll know it works when:**
- [ ] Buyer receives message from farmer
- [ ] Popup appears automatically (no page refresh needed)
- [ ] Popup is on ANY page (not just /chat/)
- [ ] Full conversation history visible in popup
- [ ] Messages update in real-time (1 sec refresh)
- [ ] Multiple popups can stack (up to 3)
- [ ] Farmer also sees popups from buyer replies
- [ ] No JavaScript errors in console
- [ ] No Django errors in server logs
