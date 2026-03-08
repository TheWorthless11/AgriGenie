"""
Quick test to verify email sending works in development mode.
Run this to test: python test_email.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriGenie.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from users.models import EmailPhoneVerification

def test_email():
    print("=" * 60)
    print("🧪 Testing Email Configuration")
    print("=" * 60)
    
    print(f"\n📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📁 Email File Path: {settings.EMAIL_FILE_PATH}")
    print(f"📌 Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    # Test sending an email
    test_email_address = "test@example.com"
    test_otp = "123456"
    
    print(f"\n📤 Sending test OTP email to {test_email_address}...")
    
    subject = "Test OTP - AgriGenie"
    message = f"""
    Test OTP Code: {test_otp}
    
    This is a test email to verify the email configuration is working.
    print("OTP/email/phone verification system has been removed.")
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [test_email_address],
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
        print(f"\n📁 Check the 'sent_emails' folder for the saved email.")
        print(f"📁 Location: {settings.EMAIL_FILE_PATH}")
        # List files in sent_emails
        import os
        if os.path.exists(settings.EMAIL_FILE_PATH):
            files = os.listdir(settings.EMAIL_FILE_PATH)
            if files:
                print(f"\n📋 Files in sent_emails folder:")
                for f in sorted(files, reverse=True)[:5]:  # Show last 5
                    print(f"   - {f}")
            else:
                print("\n❌ Folder exists but no files yet.")
        
        print("\n" + "=" * 60)
        print("✅ Email configuration is working!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("\n" + "=" * 60)
        print("❌ Please check your email configuration.")
        print("=" * 60)

if __name__ == '__main__':
    test_email()
