# 📝 New Registration Flow Documentation

## Overview

AgriGenie now supports a **flexible registration system** where users can:

1. **Register first** - Create account immediately with username, email, and password
2. **Verify anytime** - Verify email or phone number later using OTP (One-Time Password)

This allows users to get started immediately without waiting for verification, while still maintaining security through optional email/phone verification.

---

## Registration Flow

### Step 1: Direct Registration

**URL:** `/register/`

Users can register directly without needing to verify anything first:

- Username (required, unique)
- Email (required, unique)
- First Name (optional)
- Last Name (optional)
- Role (Farmer or Buyer)
- Password (required, 8+ characters)
- Confirm Password (required)

After successful registration, users are redirected to login page.

### Step 2: Verify Contact Information (Optional but Recommended)

**URL:** `/verify-contact/`

Once logged in, users can verify their email or phone number anytime:

- **Email Verification**: Users receive OTP via email
- **Phone Verification**: OTP is displayed (or sent via SMS in production)

Users can skip verification or do it later from their dashboard.

---

## User Model Changes

The `CustomUser` model now has two new fields:

```python
email_verified = models.BooleanField(default=False)  # Email verification status
phone_verified = models.BooleanField(default=False)  # Phone verification status
```

- `email_verified`: Tracks if user's email has been verified
- `phone_verified`: Tracks if user's phone has been verified

---

## API Endpoints

### Registration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register/` | GET, POST | Register new account |
| `/login/` | GET, POST | Login to account |
| `/logout/` | GET | Logout user |

### Verification (Post-Registration)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/verify-contact/` | GET | View verification status for email & phone |
| `/verify-contact/send-email-otp/` | POST | Send OTP to email |
| `/verify-contact/verify-email-otp/` | GET, POST | Verify OTP for email |
| `/verify-contact/send-phone-otp/` | POST | Send OTP to phone |
| `/verify-contact/verify-phone-otp/` | GET, POST | Verify OTP for phone |

---

## Verification Process

### Email Verification

1. User clicks "Send Verification OTP" for email
2. OTP is generated and sent to user's email
3. User enters the 6-digit OTP on `/verify-contact/verify-email-otp/`
4. System validates OTP and marks email as verified
5. User's `email_verified` field is set to `True`

### Phone Verification

1. User clicks "Send Verification OTP" for phone
2. OTP is generated and displayed (or sent via SMS in production)
3. User enters the 6-digit OTP on `/verify-contact/verify-phone-otp/`
4. System validates OTP and marks phone as verified
5. User's `phone_verified` field is set to `True`

---

## Development Testing

### Getting OTP Codes

During development, OTP codes are saved to files. To retrieve them:

```bash
# Run this command in a new terminal
py check_otp.py
```

This will display all OTP codes that were sent during registration/verification.

**Output Example:**
```
📧 AGRIGENIE - OTP CODES FROM REGISTRATION EMAILS
============================================================

📩 Email to: user@example.com
⏰ Sent at: 20260209-143022-123456.log
🔐 OTP Code: 654321
📄 File: 20260209-143022-123456.log

✅ Use the OTP codes above in the verification step!
```

### Alternative: Check sent_emails Folder

OTP emails are also saved in the `sent_emails/` folder:

```
sent_emails/
├── 20260209-143022-123456.log
├── 20260209-143023-234567.log
└── ...
```

Open any `.log` file to see the OTP code.

---

## Forms

### CustomUserCreationForm

Updated to support the new registration flow:

```python
fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
```

**Key Changes:**
- `email` field is now required and unique
- Validates that email hasn't been registered
- Sets `email_verified = False` and `phone_verified = False` when user is created

### OTPVerificationForm

Used for verifying OTP codes:

```python
otp = forms.CharField(max_length=6, min_length=6)
```

- Accepts 6-digit OTP code
- Auto-formats input to allow only digits

---

## Templates

### `/templates/users/register.html`

- Updated to direct registration without OTP
- Collects email during registration
- Shows role selection (Farmer/Buyer)

### `/templates/users/verify_contact_info.html` (NEW)

- Shows verification status for email and phone
- Displays buttons to send OTP for each contact method
- Shows which contact info is verified/unverified

### `/templates/users/verify_otp_form.html` (NEW)

- Clean form for entering 6-digit OTP
- Shows which contact method (email/phone) is being verified
- Auto-formats input to digits only
- Shows development mode OTP hint

---

## User Journey Examples

### Example 1: Complete Registration & Verification

```
1. User visits /register/
2. Fills form: username, email, password, role
3. Clicks "Create Account"
4. Redirected to /login/ with success message
5. User logs in
6. User goes to /verify-contact/
7. Clicks "Send Verification OTP" for email
8. Receives OTP in email (or check py check_otp.py)
9. Enters OTP on /verify-contact/verify-email-otp/
10. Email marked as verified
11. Dashboard shows "Email ✓ Verified"
```

### Example 2: Register Without Verification

```
1. User visits /register/
2. Fills form and creates account
3. Logs in and starts using the app
4. (Optional) Verifies email later from dashboard
```

### Example 3: Verify Phone Later

```
1. User registers and logs in
2. User goes to /verify-contact/
3. User clicks "Send Verification OTP" for phone
4. OTP displayed or sent to phone
5. User enters OTP
6. Phone marked as verified
```

---

## Settings Configuration

### Email Settings

For email verification to work, configure Django email settings in `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')
DEFAULT_FROM_EMAIL = 'agrigenie@example.com'

# For production SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
```

### SMS Settings (Future)

For phone verification in production, integrate SMS service:

```python
# Example: Twilio
TWILIO_ACCOUNT_SID = 'your-account-sid'
TWILIO_AUTH_TOKEN = 'your-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
```

---

## Security Considerations

### OTP Security

- OTP valid for **10 minutes** by default
- Each OTP is a random 6-digit code
- OTP is deleted after successful verification
- OTP expires automatically

### Password Security

- Django's default password validators apply
- Minimum 8 characters recommended
- Must include uppercase, lowercase, numbers

### Email Uniqueness

- Email must be unique across the system
- Prevents duplicate registrations
- Users can change email in profile (requires reverification)

---

## Troubleshooting

### "OTP has expired"

- OTP codes are valid for 10 minutes
- Request a new OTP and verify quickly

### "This email is already registered"

- The email already exists in the system
- Use a different email or login if it's your account

### "Invalid OTP"

- Check that you entered the code correctly
- OTP is case-sensitive (digits only)
- Can copy-paste from email or `py check_otp.py` output

### "OTP not received"

**For Development:**
```bash
py check_otp.py
# Check the sent_emails/ folder
```

**For Production:**
- Check spam/junk folder
- Verify email configuration in settings
- Check SMS provider settings for phone OTP

---

## Future Enhancements

1. **Two-Factor Authentication (2FA)**
   - Require both email and phone verification
   - Optional 2FA for high-security accounts

2. **SMS Integration**
   - Integrate Twilio or similar for SMS OTP
   - Currently shows OTP in interface during development

3. **Biometric Verification**
   - Fingerprint/Face ID for mobile apps
   - Passwordless login options

4. **Email/Phone Change**
   - Allow users to update email/phone
   - Automatic reverification required

5. **Backup Verification Methods**
   - Security questions
   - Recovery codes
   - Trusted device management

---

## Database Migration

To apply the new fields to your database:

```bash
# Create migration
py manage.py makemigrations

# Apply migration
py manage.py migrate
```

The migration will add:
- `email_verified` (BooleanField, default=False)
- `phone_verified` (BooleanField, default=False)

---

## Quick Reference

| Task | URL |
|------|-----|
| Register new account | `/register/` |
| Verify email/phone | `/verify-contact/` |
| Verify email OTP | `/verify-contact/verify-email-otp/` |
| Verify phone OTP | `/verify-contact/verify-phone-otp/` |
| Login | `/login/` |
| Dashboard | `/dashboard/` |

---

## Support

For questions or issues with the registration system:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [OTP_GUIDE.md](OTP_GUIDE.md)
3. Check Django logs: `py manage.py runserver`

