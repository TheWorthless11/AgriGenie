# 🎯 Quick Start Guide - OTP Registration

## ✅ Status: Email Configuration is WORKING!

Your development environment is set up to:
- ✅ Save all OTP emails to the `sent_emails` folder
- ✅ Automatically extract OTP codes
- ✅ Display them in a user-friendly format

---

## 📝 Steps to Register with OTP

### 1. Start the Django Server
```bash
py manage.py runserver
```
Then open: http://localhost:8000

### 2. Go to Register Page
```
http://localhost:8000/register/
```

### 3. Choose Email or Phone
- **Email:** Enter your email address
- **Phone:** Select country → Enter phone number

### 4. Click "Send OTP"

### 5. **GET YOUR OTP CODE** - Run This Command

Open a **NEW terminal** in the project folder and run:
```bash
py check_otp.py
```

You'll see something like:
```
📧 AGRIGENIE - OTP CODES FROM REGISTRATION EMAILS
============================================================

📩 Email to: your_email@example.com
⏰ Sent at: 20260127-230909-2607485755200.log
🔐 OTP Code: 654321
📄 File: 20260127-230909-2607485755200.log

✅ Use the OTP codes above in the verification step!
============================================================
```

### 6. Copy the OTP Code
Copy the 6-digit code (e.g., `654321`)

### 7. Paste in Verification Page
Go back to your browser and paste the code in the OTP field

### 8. Complete Registration
Create your username, password, and select your role (Farmer/Buyer)

---

## 📂 Available Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `check_otp.py` | 📧 Extract OTP from saved emails | `py check_otp.py` |
| `test_email.py` | 🧪 Test email configuration | `py test_email.py` |
| `manage.py runserver` | 🚀 Start Django server | `py manage.py runserver` |

---

## 📁 Where Are the Emails Saved?

```
agrigenie/
├── sent_emails/          ← All registration emails are here
│   ├── 20260127-230909-2607485755200.log
│   ├── 20260127-231015-2608392843221.log
│   └── ...
└── check_otp.py          ← Script to read them
```

---

## 🎯 Common Questions

### Q: Where do I find the OTP code?
**A:** Run `py check_otp.py` in a terminal - it will display the code.

### Q: Why isn't the email in my inbox?
**A:** In development, emails are **SAVED** to a folder, not sent to your real email. This is by design! It keeps development simple without needing email credentials.

### Q: How do I test with real emails?
**A:** See the `EMAIL_CONFIGURATION.md` file for production setup with Gmail SMTP.

### Q: Can I use my real email?
**A:** For development: No, emails are only saved locally. For production: Yes, after SMTP setup.

### Q: How long is the OTP valid?
**A:** 10 minutes from when it was sent.

### Q: Can I resend the OTP?
**A:** Yes, go back and click "Send OTP" again. A new code will be generated.

---

## ✨ Summary

1. **Register** → http://localhost:8000/register/
2. **Send OTP** → Click "Send OTP" button
3. **Get Code** → Run `py check_otp.py`
4. **Verify** → Paste code in verification page
5. **Complete** → Set username & password → Done! 🎉

---

## 🚀 Next Steps

After successful registration:
- Login with your credentials
- Complete your profile
- Start using AgriGenie!

For more details, see:
- `OTP_GUIDE.md` - Detailed OTP troubleshooting
- `EMAIL_CONFIGURATION.md` - Production email setup
