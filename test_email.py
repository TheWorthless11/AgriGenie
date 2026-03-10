"""
Quick test to verify email sending works with your Gmail SMTP.
Run this to test: python test_email.py
"""

import os
import django

# 1. Point to your new Level 2 settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    print("=" * 60)
    print("🧪 Testing Email Configuration (Gmail SMTP)")
    print("=" * 60)
    
    # Show current settings so you know it's reading the .env correctly
    print(f"\n📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📌 Default From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🌐 Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    
    # ==========================================
    # ⚠️ Change this to your personal email to test!
    # ==========================================
    test_email_address = "mahhiamim@gmail.com" 
    
    print(f"\n📤 Attempting to send a real test email to {test_email_address}...")
    
    subject = "Test Email - AgriGenie Success!"
    message = """
    Hello from AgriGenie!
    
    If you are reading this in your inbox, your Django .env email 
    configuration (Gmail SMTP) is working perfectly. 
    
    Great job setting up the backend!
    
    - The AgriGenie System
    """
    
    try:
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email_address],
            fail_silently=False,
        )
        print("\n✅ SUCCESS: Email sent without errors!")
        print("📥 Check your Gmail inbox (and Spam folder just in case).")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: Could not send email.")
        print(f"Details: {e}")
        print("\n" + "=" * 60)
        print("💡 TIP: If you get an 'Authentication Error', double-check your")
        print("EMAIL_HOST_PASSWORD in the .env file. Make sure it is a 16-letter")
        print("Google App Password, not your normal Gmail password.")
        print("=" * 60)

if __name__ == '__main__':
    test_email()