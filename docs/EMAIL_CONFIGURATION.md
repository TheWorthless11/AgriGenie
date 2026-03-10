# Email Configuration Guide for AgriGenie

## Development Setup (Console Backend - For Testing)

By default, the project uses Django's console email backend which prints OTP codes to the terminal.

### Steps to Test Email Registration:

1. **Start the Django server:**
   ```bash
   py manage.py runserver
   ```

2. **Go to registration:** http://localhost:8000/register/

3. **Choose Email verification** and enter your email

4. **Check the Django console output** - you'll see the OTP code printed there:
   ```
   ✓ OTP email sent to your_email@example.com with code: 123456
   ```

5. **Use that code** in the verification page

---

## Production Setup (Gmail SMTP)

To send real emails in production:

### 1. Create a Gmail App Password:

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Select **Security** from the left menu
3. Enable **2-Step Verification** if not already enabled
4. Find **App passwords** under "How you sign in to Google"
5. Select **Mail** and **Windows Computer** (or your device)
6. Google will generate a 16-character password

### 2. Update `.env` file:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_character_app_password
```

### 3. Update `settings.py` to use environment variables:

The project already supports this. Just create a `.env` file and the settings will load it.

---

## Alternative Email Services

### SendGrid:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
```

### AWS SES:
```bash
pip install django-ses
```

```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = 'your_key'
AWS_SECRET_ACCESS_KEY = 'your_secret'
AWS_SES_REGION_NAME = 'us-east-1'
```

### Mailgun:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your_domain.mailgun.org
EMAIL_HOST_PASSWORD=your_mailgun_password
```

---

## SMS Configuration for Phone OTP

Currently, phone OTP shows a test message in the console. To enable real SMS:

### Twilio Setup:

1. **Install Twilio:**
   ```bash
   pip install twilio
   ```

2. **Update `users/views.py`:**
   ```python
   from twilio.rest import Client
   
   def send_otp_sms(phone_number, otp):
       client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
       message = client.messages.create(
           body=f'Your AgriGenie OTP is: {otp}',
           from_=TWILIO_PHONE_NUMBER,
           to=phone_number
       )
       return message.sid
   ```

3. **Set environment variables:**
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   ```

---

## Testing Email in Development

Without configuring SMTP, you can:

1. **Use Django's FileBackend to save emails:**
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
   EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
   ```

2. **Use MailHog or Similar Tools:**
   - Download MailHog from https://github.com/mailhog/MailHog
   - Run it: `./mailhog`
   - Access the UI at http://localhost:1025
   - Configure Django to use it

3. **Use Mailtrap:**
   - Sign up at https://mailtrap.io
   - Get SMTP credentials
   - Update your `.env` file

---

## Troubleshooting

### OTP not received:
1. Check Django console output first (development mode)
2. Verify email address is correct
3. Check spam/junk folder
4. Check email backend configuration

### "SMTPAuthenticationError":
- Verify your email credentials
- For Gmail, ensure you're using an App Password, not your regular password
- Check that 2-Step Verification is enabled

### "Connection refused":
- Verify SMTP host and port are correct
- Check firewall settings
- Ensure you have internet connectivity

---

## Current Status

- **Development:** Uses console backend (OTP printed to terminal)
- **Phone Numbers:** Shows test message in console (Twilio integration needed for production)
- **Email Domains:** Supports Gmail, SendGrid, AWS SES, Mailgun, etc.
