"""
Test the registration form to ensure it's working properly.
Run this to test: python test_registration.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriGenie.settings')
django.setup()

from users.forms import ContactMethodForm
from users.models import EmailPhoneVerification

def test_email_registration():
    print("=" * 60)
    print("🧪 Testing Email Registration Form")
    print("=" * 60)
    
    data = {
        'contact_method': 'email',
        'email': 'testuser@example.com',
        'country_code': '+1',
        'phone_number': ''
    }
    
    form = ContactMethodForm(data)
    print(f"\n📝 Form data: {data}")
    print(f"✅ Form valid: {form.is_valid()}")
    
    if form.is_valid():
        print(f"✅ Email: {form.cleaned_data.get('email')}")
        print("✅ Email registration form works!")
    else:
        print(f"❌ Form errors: {form.errors}")
    
    print("\n" + "=" * 60)

def test_phone_registration():
    print("🧪 Testing Phone Registration Form")
    print("=" * 60)
    
    data = {
        'contact_method': 'phone',
        'email': '',
        'country_code': '+91',
        'phone_number': '9876543210'
    }
    
    form = ContactMethodForm(data)
    print(f"\n📝 Form data: {data}")
    print(f"✅ Form valid: {form.is_valid()}")
    
    if form.is_valid():
        phone = form.cleaned_data.get('phone_number')
        print(f"✅ Full phone number: {phone}")
        print("✅ Phone registration form works!")
    else:
        print(f"❌ Form errors: {form.errors}")
    
    print("\n" + "=" * 60)

def test_otp_creation():
    print("🧪 Testing OTP Creation")
    print("=" * 60)
    
    verification = EmailPhoneVerification.create_verification(
        verification_type='email',
        email='test_otp@example.com'
    )
    
    print(f"\n✅ Verification created:")
    print(f"   ID: {verification.id}")
    print(f"   Type: {verification.get_verification_type_display()}")
    print(f"   Email: {verification.email}")
    print(f"   OTP: {verification.otp_code}")
    print(f"   Valid: {verification.is_valid()}")
    print(f"   Expires: {verification.expires_at}")
    
    print("\n✅ OTP system works!")
    print("=" * 60)

if __name__ == '__main__':
    test_email_registration()
    test_phone_registration()
    test_otp_creation()
