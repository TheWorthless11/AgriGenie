"""
Test the Dynamic Registration Form to ensure it's working properly.
Run this to test: python test_registration.py
"""

import os
import django

# Points to your Level 2 settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from users.forms import DynamicRegistrationForm

def test_farmer_registration():
    print("=" * 60)
    print("🧪 Testing Farmer Registration (PIN Auth)")
    print("=" * 60)
    
    # Simulating a Farmer signing up from Dhaka
    data = {
        'full_name': 'Rahim Mia',
        'phone_number': '+8801712345678',
        'role': 'farmer',
        'district': 'Dhaka',
        'upazila': 'Sadar',
        'country': 'Bangladesh',
        'auth_type': 'pin',
        'pin': '1234',
        'confirm_pin': '1234'
    }
    
    form = DynamicRegistrationForm(data)
    print(f"\n📝 Form data: Farmer from {data['district']}")
    print(f"✅ Form valid: {form.is_valid()}")
    
    if form.is_valid():
        print("✅ Farmer registration logic works perfectly!")
    else:
        print(f"❌ Form errors: {form.errors}")
    
    print("\n" + "=" * 60)

def test_buyer_registration():
    print("🧪 Testing Buyer Registration (Password Auth)")
    print("=" * 60)
    
    # Simulating a Buyer signing up from Chittagong
    data = {
        'full_name': 'AgroCorp BD',
        'phone_number': '+8801812345679',
        'role': 'buyer',
        'district': 'Chittagong',
        'upazila': 'North',
        'country': 'Bangladesh',
        'email': 'buyer@agrocorp.bd',
        'password': 'StrongPassword123',
        'confirm_password': 'StrongPassword123'
    }
    
    form = DynamicRegistrationForm(data)
    print(f"\n📝 Form data: Buyer from {data['district']}")
    print(f"✅ Form valid: {form.is_valid()}")
    
    if form.is_valid():
        print("✅ Buyer registration logic works perfectly!")
    else:
        print(f"❌ Form errors: {form.errors}")
    
    print("\n" + "=" * 60)

def test_otp_and_token_system():
    print("🧪 Testing Forgot Credential System")
    print("=" * 60)
    
    try:
        from users.models import OTPVerification, PasswordResetToken, CustomUser
        
        # 1. Test Farmer OTP Generation
        print("\n📱 Testing Farmer OTP (Phone):")
        otp = OTPVerification.generate_otp(phone_number='+8801712345678')
        print(f"   ✅ OTP Generated: {otp.otp_code}")
        print(f"   ✅ Expires at: {otp.expires_at}")
        otp.delete()
        print("   🧹 Cleaned up OTP.")

        # 2. Test Buyer Token Generation
        print("\n📧 Testing Buyer Token (Email):")
        # We need a temporary user for this test
        user, created = CustomUser.objects.get_or_create(username="testbuyer", email="buyer@test.com")
        token_obj = PasswordResetToken.generate_token(user)
        print(f"   ✅ Token Generated: {token_obj.token[:20]}...")
        print(f"   ✅ Valid: {token_obj.is_valid()}")
        
        token_obj.delete()
        if created: user.delete()
        print("   🧹 Cleaned up Token and Test User.")

        print("\n✅ OTP & Token systems are fully functional!")
        
    except ImportError as e:
        print(f"❌ Could not find models: {e}")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        
    print("=" * 60)
    
if __name__ == '__main__':
    test_farmer_registration()
    test_buyer_registration()
    test_otp_and_token_system()