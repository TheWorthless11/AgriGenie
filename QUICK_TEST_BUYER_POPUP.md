# Quick Test Guide - Buyer Popup Window

## In 5 Minutes

### Setup
1. Make sure you have at least 1 Farmer account and 1 Buyer account created

### Test Farmer (Baseline)
```
1. Login as FARMER
2. Go to Marketplace
3. Find any product/crop posted by a buyer
4. Click "Message" button
5. Type a message and send
6. You should see popup appear in bottom-right
   ✓ Popup shows buyer's name
   ✓ Popup shows conversation history
   ✓ You can reply in popup

If this works → Baseline is OK, system works for farmers
```

### Test Buyer
```
1. Login as BUYER (different browser/incognito tab)
2. Open Developer Tools: Press F12
3. Go to Console tab
4. Send a message to the BUYER from the FARMER
   (Go back to farmer tab, send message via popup)
5. Watch the BUYER's console in the other tab
6. Look for logs starting with "[Chat Popup]"
7. Check if popup appears

Expected:
  ✓ Console shows "[Chat Popup] Fetching unread conversations..."
  ✓ Console shows "Found 1 unread conversations"
  ✓ Console shows "Successfully created popup for room X"
  ✓ Popup appears in bottom-right corner with farmer's message
  ✓ Buyer can read full conversation
  ✓ Buyer can reply by typing in popup

If this works → Feature is COMPLETE ✅
```

## Detailed Checklist

### Browser Console (F12) - Should See:
```
[Chat System] Page load state: complete
[Chat System] Initializing popups and polling
[Chat System] DEBUG INFO: {...}
[Chat System] Polling started with interval: ...
[Chat Popup] Fetching unread conversations...
[Chat Popup] Response status: 200
[Chat Popup] Full API Response: {success: true, conversations: [...]}
[Chat Popup] Found 1 unread conversations
[Chat Popup] Processing conversation room_id: 123
[Chat Popup] Displaying popup for room 123
[displayChatPopup] Creating popup for room 123
[displayChatPopup] Successfully created popup for room 123
```

### If Console is Empty:
```
Check:
1. Are you logged in as buyer? (Should see login button→account menu)
2. Is F12 filter set correctly? (Filter box should be empty)
3. Try refreshing page
4. Look for JavaScript errors in console (red text)
```

### If API Returns Error:
```
Check:
1. Open Network tab in F12
2. Click on /chat/api/unread-conversations/ request
3. Check Status - should be 200 OK
4. Click Response tab - should show JSON

If Status 403: Permission denied (check decorators)
If Status 404: Route not found (check urls.py)
If 500: Server error (check Django terminal)
```

## Database Quick Check

```bash
# Run in Python:
python manage.py shell

# Then type:
from chat.models import ChatRoom, ChatMessage
from users.models import CustomUser
from django.db.models import Q

buyer = CustomUser.objects.get(username='your_buyer_username')
rooms = ChatRoom.objects.filter(Q(farmer=buyer) | Q(buyer=buyer))
print(f"Buyer has {rooms.count()} chat rooms")

for room in rooms:
    unread = room.messages.filter(is_read=False).exclude(sender=buyer)
    print(f"  Room {room.id}: {unread.count()} unread messages from {room.farmer.username if buyer == room.buyer else room.buyer.username}")
```

Expected output:
```
Buyer has 1 chat rooms
  Room 123: 1 unread messages from farmer_username
```

## Quick API Test

**Copy-paste this into browser console (F12) while logged in as buyer:**

```javascript
fetch('/chat/api/unread-conversations/')
  .then(r => {
    console.log('Status:', r.status);
    return r.json();
  })
  .then(d => {
    console.log('Response:', d);
    if (d.success && d.conversations.length > 0) {
      console.log('✅ API WORKS -', d.conversations.length, 'unread conversation(s)');
    } else {
      console.log('❌ API OK but no conversations');
    }
  })
  .catch(e => console.error('❌ API ERROR:', e));
```

Expected output:
```
Status: 200
Response: {success: true, conversations: [{room_id: 123, other_user_username: "farmer", ...}]}
✅ API WORKS - 1 unread conversation(s)
```

## Verify Each Component

### 1. Is API Accessible?
```javascript
// Console:
fetch('/chat/api/unread-conversations/').then(r => console.log('Status:', r.status))
// Should log: Status: 200
```

### 2. Does Database Have Data?
```python
# Django shell:
from chat.models import ChatRoom
ChatRoom.objects.filter(is_active=True).count()
# Should show: 1 or more
```

### 3. Does Frontend JavaScript Load?
```javascript
// Console:
typeof initializeChatSystem
// Should show: "function"
typeof fetchAndDisplayChatPopups
// Should show: "function"
```

### 4. Are Popups Rendered?
```javascript
// Console:
document.querySelectorAll('.chat-popup-window').length
// Should show: Number of open popups (e.g., 1)
```

## Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| No logs appear | Check if you're logged in; try F5 refresh |
| API returns empty | Check if ChatRoom exists in database |
| Popup doesn't appear | Check browser console for JavaScript errors |
| Popup appears but empty | Check if /chat/api/conversation/{room_id}/ works |
| Message doesn't send | Check if /chat/api/send/{room_id}/ works |

## Success = All These Work:

✅ Buyer logs in  
✅ Farmer sends message to buyer  
✅ Within 1-2 seconds, buyer sees popup (no refresh)  
✅ Popup shows full conversation  
✅ Buyer can reply in popup  
✅ Farmer sees buyer's reply in popup  
✅ No errors in console (F12)  

---

## Alternative: Run Test Script

If browser testing is complex, run this:

```bash
python manage.py shell < test_buyer_popup.py
```

This will:
- Create a test chat room if needed
- Create a test message
- Run the exact query that the API runs
- Show you what the popup would display
- Indicate if everything works

---

**Still Not Working?** 
→ Check the detailed docs in BUYER_POPUP_IMPLEMENTATION.md  
→ Follow Debugging Steps in BUYER_POPUP_VERIFICATION.md
