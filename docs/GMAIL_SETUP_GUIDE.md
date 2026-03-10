# Gmail SMTP Setup Guide for AgriGenie

Your email configuration has been updated to use Gmail SMTP for real email delivery. Follow these steps to complete the setup.

## Step 1: Create a Gmail App Password

1. **Go to Google Account Security**
   - Visit: https://myaccount.google.com/security
   - Sign in with your Gmail account

2. **Enable 2-Step Verification** (if not already enabled)
   - Click on "2-Step Verification"
   - Follow the prompts to enable it
   - This is required to generate an App Password

3. **Generate App Password**
   - Go back to Security settings
   - Scroll down and find "App passwords"
   - Select "Mail" and "Windows" (or your OS)
   - Google will generate a 16-character password (with spaces)
   - **Copy this password** - you'll need it in the next step

## Step 2: Configure Your .env File

The `.env` file has been created in your project root. Update it with your Gmail credentials:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Important:**
- Replace `your-email@gmail.com` with your actual Gmail address
- Replace `xxxx xxxx xxxx xxxx` with the 16-character App Password (include the spaces)
- Keep the spaces in the App Password - they're part of it

### Example:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=shaila@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=shaila@gmail.com
```

## Step 3: Verify the Configuration

Run the test email script to verify everything works:

```bash
python test_email.py
```

This will:
- Send a test email to your configured EMAIL_HOST_USER
- Verify SMTP connection
- Confirm OTP can be delivered

You should receive the email within 1-2 minutes. **Check your spam folder** if it doesn't appear in your inbox.

## Step 4: Test OTP Delivery

1. Go to your application (http://localhost:8000)
2. Register a new account if you haven't already
3. Navigate to Settings & Verification
4. Click "Send Email OTP"
5. Check your email for the OTP code

## Troubleshooting

### Email not received?
- **Check spam folder** - Gmail sometimes filters automated emails
- **Verify credentials** - Double-check your App Password in .env
- **Check Django logs** - Look for any error messages when sending

### "Login credentials invalid"?
- App Password must be the 16-character one from Google Account
- Regular Gmail password won't work
- Ensure you enabled 2-Step Verification first

### Connection refused?
- Verify EMAIL_PORT is 587 (not 465 or 25)
- Check EMAIL_USE_TLS is True
- Ensure Gmail credentials are correct

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to version control
- The `.env` file is already in `.gitignore`
- App Password is specific to your application - you can revoke it anytime
- Store these credentials securely - don't share them

## What Changed

The email configuration was updated from **file-based backend** (development mode) to **SMTP backend** (production mode):

**Before (Development):**
- Emails saved to `sent_emails/` folder
- No actual email delivery
- Used for testing without real email service

**After (Production):**
- Emails sent via Gmail SMTP servers
- Real email delivery to user inboxes
- OTP codes actually sent to users

## Next Steps

1. ✅ python-decouple installed
2. ✅ settings.py updated with SMTP configuration
3. ⬜ Add Gmail credentials to .env file (YOUR TURN)
4. ⬜ Test email sending with test_email.py
5. ⬜ Verify OTP delivery in your application

---

**Questions?** Check the [settings.py](AgriGenie/settings.py) email configuration or [.env](.env) template for details.
