# 📋 Registration System - Visual Guide & Checklists

## Registration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REGISTRATION FLOW                        │
└─────────────────────────────────────────────────────────────────┘

                              START
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Visit /register/    │
                    └─────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────────────┐
                    │ Fill Registration Form:              │
                    │ • Username (required, unique)        │
                    │ • Email (required, unique)           │
                    │ • First Name (optional)              │
                    │ • Last Name (optional)               │
                    │ • Password (required, 8+ chars)      │
                    │ • Role: Farmer / Buyer               │
                    └──────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Click "Create       │
                    │ Account"            │
                    └─────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ✓ Success            ✗ Form Invalid
        │                    │
        ▼                    └─► Show Error Messages
    Account Created
    │
    ▼
┌────────────────────────┐
│ Redirect to Login      │
│ "Account created!"     │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│ Login with             │
│ Username + Password    │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│ Redirect to Dashboard  │
│ Account Active!        │
└────────────────────────┘
    │
    └─────────────────────────────┐
                                  │
                       (OPTIONAL VERIFICATION)
                                  │
                    ┌─────────────▼──────────────┐
                    │ Visit /verify-contact/     │
                    │ Check verification status  │
                    └─────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
            EMAIL         or  PHONE      or  SKIP
            │                 │              │
            ▼                 ▼              ▼
        Send OTP to       Send OTP to    Continue
        Email             Phone          Using App
        │                 │
        ▼                 ▼
    Receive OTP       Receive OTP
    (check_otp.py)    (check_otp.py)
        │                 │
        ▼                 ▼
    Enter OTP          Enter OTP
        │                 │
        ▼                 ▼
    ✓ Verified!        ✓ Verified!
```

---

## User Actions Checklist

### ✅ To Register

- [ ] Go to `/register/`
- [ ] Enter username (unique)
- [ ] Enter email (unique)
- [ ] Enter password (8+ characters)
- [ ] Select role (Farmer or Buyer)
- [ ] Click "Create Account"
- [ ] See success message
- [ ] Proceed to login

### ✅ To Verify Email

- [ ] Login to account
- [ ] Go to `/verify-contact/`
- [ ] Click "Send Verification OTP" for Email
- [ ] See message: "OTP sent to your email"
- [ ] Run `py check_otp.py` (development)
- [ ] Copy OTP code
- [ ] Enter 6-digit OTP
- [ ] Click "Verify OTP"
- [ ] See "Email verified successfully!"
- [ ] Dashboard shows "Email ✓ Verified"

### ✅ To Verify Phone

- [ ] Login to account
- [ ] Go to `/verify-contact/`
- [ ] Click "Send Verification OTP" for Phone
- [ ] See message: "OTP Code: XXXXXX"
- [ ] Enter 6-digit OTP
- [ ] Click "Verify OTP"
- [ ] See "Phone verified successfully!"
- [ ] Dashboard shows "Phone ✓ Verified"

---

## Developer Setup Checklist

### ✅ Initial Setup

- [ ] Clone or have AgriGenie project open
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with settings (if needed)
- [ ] Start Redis: `redis-server`

### ✅ Database Setup

- [ ] Run migrations: `py manage.py makemigrations`
- [ ] Apply migrations: `py manage.py migrate`
- [ ] Create superuser: `py manage.py createsuperuser` (optional)
- [ ] Verify database created: `db.sqlite3` exists

### ✅ Server Setup

- [ ] Start Django server: `py manage.py runserver`
- [ ] Access at: `http://localhost:8000`
- [ ] Check home page loads
- [ ] Test `/register/` page loads

### ✅ Test Registration Flow

- [ ] Go to `/register/`
- [ ] Create test account with unique email
- [ ] Verify redirect to login
- [ ] Login with credentials
- [ ] Verify dashboard loads
- [ ] Go to `/verify-contact/`
- [ ] Request email OTP
- [ ] Run `py check_otp.py`
- [ ] Enter OTP and verify
- [ ] Check email shows as verified

### ✅ Test Phone Verification

- [ ] From `/verify-contact/`
- [ ] Click "Send Verification OTP" for Phone
- [ ] See OTP displayed on page
- [ ] Enter OTP and verify
- [ ] Check phone shows as verified

---

## Email Setup Checklist

### ✅ Development (File-based)

- [ ] `EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'`
- [ ] `EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')`
- [ ] `sent_emails/` folder exists
- [ ] Can view `.log` files in `sent_emails/`
- [ ] `check_otp.py` script works

### ✅ Production (SMTP)

- [ ] Gmail account or SMTP server ready
- [ ] `EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'`
- [ ] `EMAIL_HOST = 'smtp.gmail.com'` (or your server)
- [ ] `EMAIL_PORT = 587`
- [ ] `EMAIL_USE_TLS = True`
- [ ] `EMAIL_HOST_USER = 'your-email@gmail.com'`
- [ ] `EMAIL_HOST_PASSWORD = 'app-password'` (not gmail password)
- [ ] Test email sending works
- [ ] Monitor email delivery

---

## Troubleshooting Checklist

### ❓ Issue: "This email is already registered"

- [ ] Verify email hasn't been used before
- [ ] Check database for existing email
- [ ] Use different email
- [ ] Or reset that user and register again

### ❓ Issue: "OTP has expired"

- [ ] OTP valid for 10 minutes
- [ ] Request new OTP immediately
- [ ] Complete verification quickly

### ❓ Issue: "Invalid OTP"

- [ ] Check digits are correct
- [ ] No spaces in OTP
- [ ] Copy from `check_otp.py` output
- [ ] Check expiration time

### ❓ Issue: "OTP not received by email"

- [ ] Development mode: check `sent_emails/` folder
- [ ] Development mode: run `py check_otp.py`
- [ ] Production: check spam folder
- [ ] Check SMTP settings
- [ ] Check email logs

### ❓ Issue: "Database migration errors"

- [ ] Run: `py manage.py makemigrations`
- [ ] Run: `py manage.py migrate`
- [ ] Check for existing migrations
- [ ] May need to reset database for testing

### ❓ Issue: "Templates not found"

- [ ] Check template path: `templates/users/`
- [ ] Verify file names match exactly
- [ ] Check settings.py TEMPLATES configuration
- [ ] Run `py manage.py collectstatic` (production)

---

## Testing Scenarios

### 🧪 Scenario 1: Complete Registration & Verification

```
1. Register: username=farmer1, email=farmer1@test.com
2. Password: Test123456 (8+ chars, mixed case)
3. Role: Farmer
4. Submit → Redirected to login
5. Login: farmer1 / Test123456
6. Verify email: /verify-contact/ → Send OTP
7. Check: py check_otp.py
8. Enter OTP: 123456
9. Email verified ✓
10. Check dashboard: Email ✓ Verified
```

### 🧪 Scenario 2: Register Without Verification

```
1. Register: username=buyer1, email=buyer1@test.com
2. Submit → Redirected to login
3. Login: buyer1 / Test123456
4. Dashboard shows Email: ⚠ Not Verified
5. Skip verification for now
6. Use app features immediately
7. Verify later when ready
```

### 🧪 Scenario 3: Phone Verification

```
1. Login to existing account
2. Go to /verify-contact/
3. Click "Send OTP" for Phone
4. Page shows OTP: 654321
5. Enter OTP: 654321
6. Phone verified ✓
```

### 🧪 Scenario 4: Error Handling

```
1. Try register with duplicate email → Error shown
2. Try OTP with wrong code → Error shown
3. Try OTP after expiration → Redirect to re-request
4. Try access verify without login → Redirect to login
```

---

## Performance Checklist

### ⚡ Database

- [ ] Indexes on email field (uniqueness)
- [ ] Indexes on username field (uniqueness)
- [ ] Queries optimized for user lookup
- [ ] No N+1 queries in verification flow

### ⚡ OTP Generation

- [ ] OTP generated in < 10ms
- [ ] Verification lookup fast
- [ ] Expires after 10 minutes
- [ ] Old OTPs cleaned up

### ⚡ Email Sending

- [ ] Development: instant file save
- [ ] Production: < 5 second delivery
- [ ] Async email sending (Celery)
- [ ] Retry mechanism for failures

### ⚡ Templates

- [ ] Pages load < 1 second
- [ ] No blocking JavaScript
- [ ] Mobile responsive
- [ ] Bootstrap 5 optimized

---

## Security Checklist

### 🔒 Authentication

- [ ] Passwords hashed (Django default)
- [ ] CSRF protection enabled
- [ ] Login required for verification
- [ ] Session timeout configured

### 🔒 OTP Security

- [ ] OTP random 6-digit codes
- [ ] OTP valid for 10 minutes only
- [ ] OTP deleted after use
- [ ] No OTP in logs or error messages
- [ ] OTP not sent via URL parameters

### 🔒 Email Security

- [ ] Email field unique
- [ ] Email validation on registration
- [ ] Email ownership verified via OTP
- [ ] Email change requires reverification

### 🔒 Password Security

- [ ] Minimum 8 characters
- [ ] Must use Django validators
- [ ] No common passwords
- [ ] Cannot be username
- [ ] Hashed in database

---

## Deployment Checklist

### 📦 Pre-Deployment

- [ ] All tests passing
- [ ] No DEBUG=True in production
- [ ] ALLOWED_HOSTS configured
- [ ] SECRET_KEY changed
- [ ] Database configured
- [ ] Email backend configured

### 📦 Post-Deployment

- [ ] Test registration works
- [ ] Test email OTP sending
- [ ] Test phone OTP verification
- [ ] Monitor error logs
- [ ] Check email delivery rates
- [ ] Verify SSL/HTTPS

### 📦 Maintenance

- [ ] Monitor OTP success rate
- [ ] Check email delivery failures
- [ ] Review user feedback
- [ ] Update documentation
- [ ] Track verification rates

---

## Documentation Links

| Document | Purpose |
|----------|---------|
| [REGISTRATION_FLOW.md](REGISTRATION_FLOW.md) | Complete registration guide |
| [OTP_GUIDE.md](OTP_GUIDE.md) | How to get OTP codes |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | What was changed |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | API reference |

---

## Quick Commands

```bash
# Start server
py manage.py runserver

# Create migrations
py manage.py makemigrations

# Apply migrations
py manage.py migrate

# Get OTP codes (development)
py check_otp.py

# Create superuser
py manage.py createsuperuser

# Run tests
py manage.py test

# Collect static files
py manage.py collectstatic
```

---

**Last Updated:** February 9, 2026
**Status:** ✅ Complete

