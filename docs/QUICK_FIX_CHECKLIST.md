# ⚡ Quick Fix Checklist

## Issues Fixed ✅

- [x] Dashboard missing `days_remaining` variable → **FIXED in users/views.py**
- [x] Django configuration errors → **VERIFIED - No issues**
- [x] Email backend configuration → **SWITCHED to SMTP**
- [x] Python-decouple integration → **INSTALLED and INTEGRATED**

---

## Issues Remaining (Need Your Action)

- [ ] OTP still showing on website (waiting for real Gmail credentials)

---

## What You Need to Do (3 Steps)

### Step 1: Get Gmail App Password
```
Visit: https://myaccount.google.com/security
→ Enable "2-Step Verification" (if needed)
→ Find "App passwords"
→ Select "Mail" and "Windows"
→ Generate password
→ Copy 16-char password (e.g., abcd efgh ijkl mnop)
```

### Step 2: Update `.env` File
Open `.env` and change:
```
EMAIL_HOST_USER=your-actual-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-password
DEFAULT_FROM_EMAIL=your-actual-email@gmail.com
```

### Step 3: Restart Server
```bash
# Stop current server (Ctrl+C)
# Then restart:
python manage.py runserver
```

---

## Test Instructions

1. Log in to your app
2. Go to **Settings & Verification** page
3. Click **"Send Email OTP"**
4. Check your email inbox (and spam folder)
5. You should receive the OTP within 1-2 minutes

---

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| Django Server | ✅ Running | http://127.0.0.1:8000/ |
| Database | ✅ Ready | Migrations applied |
| Settings Page | ✅ Working | All context variables present |
| Dashboard | ✅ Working | Fixed days_remaining issue |
| Email Sending | ⏳ Waiting | Need Gmail credentials |
| OTP Display | ⏳ Fallback | Shows code until email working |

---

## Files You Need to Edit

**File:** `.env` (in project root)
**Lines to update:**
- Line 20: `EMAIL_HOST_USER=...`
- Line 21: `EMAIL_HOST_PASSWORD=...`
- Line 22: `DEFAULT_FROM_EMAIL=...`

That's it! All code changes are done. Just need your email credentials.
