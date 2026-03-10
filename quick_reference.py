#!/usr/bin/env python
"""
Quick reference for the current AgriGenie project.
Updated: 2026 - aligned with the active Django codebase.
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║               AGRIGENIE QUICK REFERENCE 2026                 ║
╚════════════════════════════════════════════════════════════════╝

1. STARTUP STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Core runtime:
    - Django app server on http://127.0.0.1:8000/
    - MySQL configured from .env (commonly via XAMPP locally)
    - Redis for cache, Channels, and Celery-backed background work

  Common local commands:
    - .venv\\Scripts\\activate
    - python manage.py runserver
    - celery -A AgriGenie worker -l info
    - celery -A AgriGenie beat -l info


2. APP MAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  users/         Authentication, registration, profiles, notifications,
                 forgot PIN/password, Google role selection.
  farmer/        Crop management, orders received, disease detection,
                 price prediction, weather alerts, farmer messaging.
  buyer/         Marketplace browsing, orders, wishlist, saved crops,
                 contact farmer, reviews, purchase history.
  marketplace/   Public crop discovery, search, reviews, storefronts.
  admin_panel/   User approvals, user management, master crops,
                 AI monitoring, reports, alerts, activity logs.
  chat/          Direct farmer-buyer chat with AJAX fallback + Channels.
  ai_models/     Disease detection, weather service, price prediction.


3. REGISTRATION AND LOGIN FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Standard registration: /register/

  Farmer account:
    - Requires full name, phone, district, upazila, country.
    - Auth type can be PIN or password.
    - PIN is stored hashed in pin_hash.
    - A basic FarmerProfile is auto-created after signup.
    - Default farm name becomes "[First Name]'s Farm".

  Buyer account:
    - Still requires phone during signup.
    - Email is mandatory for buyer registration and buyer login.
    - Password must be 8+ chars with upper, lower, and digit.
    - Preferences are saved on the CustomUser model.
    - A basic BuyerProfile is auto-created after signup.

  Username rule:
    - Username is auto-generated from the last 10 digits of phone.
    - If duplicated, suffixes like _1, _2 are appended.

  Login behavior: /login/
    - Farmer: phone or email + PIN/password.
    - Buyer: email + password.
    - Session cookie is explicitly set after login for ASGI/Daphne.


4. GOOGLE OAUTH FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Google auth entry: /accounts/...
  Backend: django-allauth + custom adapters.

  New social users:
    - Start with role = pending.
    - Must complete /google-role-select/.
    - Buyer path creates BuyerProfile and goes to dashboard.
    - Farmer path goes to profile edit to finish setup.


5. APPROVAL AND ACCESS CONTROL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Signup governance:
    - Every new standard signup gets a UserApproval record.
    - Default approval status is pending.
    - Admins are notified when a new approval request is created.

  Actual action gates in code:
    - Farmers cannot add, edit, or delete crops until approved.
    - Farmers cannot send direct messages until approved.
    - Buyers cannot place orders until approved.
    - Buyers cannot contact farmers until approved.
    - Buyers cannot leave reviews until approved.

  Admin control center:
    - /admin-panel/dashboard/
    - /admin-panel/approvals/
    - /admin-panel/users/
    - /admin-panel/master-crops/


6. RECOVERY AND SECURITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Farmer recovery:
    - /forgot/ -> /send-otp/ -> /verify-otp/ -> /reset-credential/
    - Uses OTPVerification with rate limiting and attempt tracking.
    - Reset supports either PIN or password.

  Buyer recovery:
    - /forgot-password/ sends a reset link by email.
    - /reset-password/<token>/ validates PasswordResetToken.
    - Reset tokens are single-use and expire server-side.

  Security notes:
    - PINs use Django password hashing helpers.
    - Passwords use Django auth hashing.
    - Forgot flows do not reveal whether an account exists.


7. CORE PRODUCT FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Farmer features:
    - Add and manage crops for sale.
    - AI disease detection on owned crops or admin-allowed master crops.
    - Crop price prediction + historical price API.
    - Weather and disaster alerts.
    - Order handling, notifications, and messaging.

  Buyer features:
    - Marketplace search and filters.
    - Place orders and confirm receipt.
    - Wishlist and saved crops.
    - Leave verified reviews after delivered orders.

  Admin features:
    - Approve/reject users.
    - Control master crop catalog.
    - Send system alerts.
    - Review user-submitted reports.
    - Monitor AI detections and generated price analytics.


8. DEBUGGING COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  python manage.py check
  python manage.py showmigrations
  python manage.py shell

  Useful shell checks:
    - user.check_pin('1234')
    - CustomUser.objects.filter(role='farmer').count()
    - UserApproval.objects.filter(status='pending').count()


9. IMPLEMENTATION NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - AI imports degrade gracefully in development if ML deps are missing.
  - Redis is part of cache + Channels + Celery configuration.
  - Media uploads include profile images, crop photos, and disease uploads.
  - The project uses a custom user model: users.CustomUser.

═══════════════════════════════════════════════════════════════════
KEY TAKEAWAY: Phone drives username generation, approval gates real actions,
and the platform spans auth, marketplace, AI tools, chat, and admin ops.
═══════════════════════════════════════════════════════════════════
""")

if __name__ == '__main__':
  import os
  import django
  import sys

  print("Running AgriGenie integrity checks...")

  base_dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(base_dir)
  if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

  try:
    django.setup()

    from django.conf import settings
    from django.db import connection
    from users.forms import DynamicRegistrationForm
    from users.models import CustomUser, FarmerProfile, BuyerProfile, OTPVerification, PasswordResetToken
    from admin_panel.models import UserApproval, MasterCrop
    from chat.models import ChatRoom
    from ai_models import analyze_disease_image, WeatherService

    connection.ensure_connection()
    print("[OK] Database connection is available")

    required_apps = ['users', 'farmer', 'buyer', 'admin_panel', 'marketplace', 'chat', 'allauth', 'channels']
    missing_apps = [app for app in required_apps if app not in settings.INSTALLED_APPS]
    if missing_apps:
      print(f"[WARN] Missing INSTALLED_APPS entries: {', '.join(missing_apps)}")
    else:
      print("[OK] Core Django apps are registered")

    print("[OK] Custom user and profile models are importable")
    print(f"[OK] Registration form detected: {DynamicRegistrationForm.__name__}")
    print(f"[OK] Approval model detected: {UserApproval.__name__}")
    print(f"[OK] Master crop model detected: {MasterCrop.__name__}")
    print(f"[OK] Recovery models detected: {OTPVerification.__name__}, {PasswordResetToken.__name__}")
    print(f"[OK] Chat model detected: {ChatRoom.__name__}")
    print(f"[OK] AI hooks detected: {analyze_disease_image.__name__}, {WeatherService.__name__}")

    print("\nArchitecture snapshot looks consistent with the current codebase.")

  except ModuleNotFoundError as e:
    print(f"\n[ERROR] Integrity check failed: missing Python package or wrong interpreter -> {e}")
    print("Use the project environment with installed requirements, then rerun this file.")
  except Exception as e:
    print(f"\n[ERROR] Integrity check failed: {e}")
    print("Check .env, database connectivity, Redis-related services, and installed apps.")