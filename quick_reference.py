#!/usr/bin/env python
"""
🎯 QUICK REFERENCE - AgriGenie OTP Registration

This file explains how OTP registration works in 2 minutes.
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║         🎯 AGRIGENIE OTP REGISTRATION - QUICK START           ║
╚════════════════════════════════════════════════════════════════╝

📋 STEP 1: START SERVER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  py manage.py runserver
  
  Then open: http://localhost:8000/register/


📋 STEP 2: REGISTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  ✓ Choose verification method:
    - Email: Enter email address
    - Phone: Select country + enter phone number
  
  ✓ Click "Send OTP"


📋 STEP 3: GET YOUR OTP CODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  In a NEW terminal, run:
  
  py check_otp.py
  
  You'll see the 6-digit OTP code displayed.


📋 STEP 4: VERIFY OTP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  ✓ Copy the OTP code
  ✓ Go back to browser
  ✓ Paste code in verification field
  ✓ Click "Verify OTP"


📋 STEP 5: CREATE ACCOUNT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  ✓ Enter username
  ✓ Choose role (Farmer or Buyer)
  ✓ Set password
  ✓ Click "Create Account"


✅ DONE! Login and start using AgriGenie 🎉


═══════════════════════════════════════════════════════════════════

💡 HELPFUL COMMANDS:

  py check_otp.py          → Get OTP codes from saved emails
  py test_email.py         → Test email configuration
  py test_registration.py  → Test registration forms
  py manage.py runserver   → Start Django server


═══════════════════════════════════════════════════════════════════

⚠️  IMPORTANT:

  • OTP expires after 10 minutes
  • Each country requires correct format
  • Use the check_otp.py script to retrieve codes
  • For production, configure SMTP credentials


═══════════════════════════════════════════════════════════════════

📁 FILES & LOCATIONS:

  Registration page:    http://localhost:8000/register/
  Saved emails:         sent_emails/ folder
  OTP checker script:   check_otp.py
  Email test script:    test_email.py
  Registration tests:   test_registration.py


═══════════════════════════════════════════════════════════════════

🌍 SUPPORTED COUNTRIES:

  USA (+1) | UK (+44) | India (+91) | China (+86) | Japan (+81)
  Germany (+49) | France (+33) | Italy (+39) | Spain (+34)
  Australia (+61) | Brazil (+55) | South Africa (+27)
  Nigeria (+234) | Pakistan (+92) | Bangladesh (+880)


═══════════════════════════════════════════════════════════════════

✨ That's it! Happy registering! 🚀

""")

if __name__ == '__main__':
    import subprocess
    import sys
    
    print("\n🔍 Running system checks...")
    
    # Test email
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        print("✅ Email system configured")
        print(f"   Backend: {settings.EMAIL_BACKEND}")
    except:
        print("❌ Email system issue")
    
    # Test forms
    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriGenie.settings')
        django.setup()
        from users.forms import ContactMethodForm
        form = ContactMethodForm({'contact_method': 'email', 'email': 'test@test.com'})
        if form.is_valid():
            print("✅ Registration forms working")
        else:
            print("❌ Form validation issue")
    except Exception as e:
        print(f"❌ Form check error: {e}")
