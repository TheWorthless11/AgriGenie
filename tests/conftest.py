"""
Pytest configuration and shared fixtures for AgriGenie tests.
Override database settings to use SQLite for tests.
"""
import os
import sys
import pytest

# Force SQLite database for tests before Django imports
os.environ.setdefault('DB_ENGINE', 'django.db.backends.sqlite3')
os.environ.setdefault('DB_NAME', ':memory:')

import django
from django.conf import settings
from django.contrib.auth import get_user_model
from users.models import FarmerProfile, BuyerProfile
from farmer.models import Crop
from admin_panel.models import MasterCrop

User = get_user_model()


def pytest_configure():
    """Configure Django test database to use SQLite"""
    # Override DATABASES to use SQLite for tests
    if hasattr(settings, 'DATABASES'):
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }


@pytest.fixture
def farmer_user(db):
    """Create a test farmer user"""
    user = User.objects.create_user(
        username='testfarmer',
        email='farmer@test.com',
        password='testpass123',
        role='farmer',
        phone_number='+8801712345678',
        district='Dhaka',
        upazila='Sadar',
        country='Bangladesh'
    )
    user.set_pin('1234')
    user.save()
    return user


@pytest.fixture
def farmer_profile(db, farmer_user):
    """Create a test farmer profile"""
    return FarmerProfile.objects.create(
        user=farmer_user,
        farm_name="Test Farm",
        farm_size=5.0,
        farm_location="Dhaka",
        soil_type="Clay",
        experience_years=10,
        registration_number="FAR-001",
        is_approved=True
    )


@pytest.fixture
def buyer_user(db):
    """Create a test buyer user"""
    return User.objects.create_user(
        username='testbuyer',
        email='buyer@test.com',
        password='testpass123',
        role='buyer',
        phone_number='+8801987654321',
        district='Chittagong',
        upazila='Kotwali',
        country='Bangladesh'
    )


@pytest.fixture
def buyer_profile(db, buyer_user):
    """Create a test buyer profile"""
    return BuyerProfile.objects.create(
        user=buyer_user,
        company_name="Agro Corp",
        business_type="Wholesale",
        registration_number="BUY-001",
        is_approved=True
    )


@pytest.fixture
def master_crop(db):
    """Create a test master crop"""
    return MasterCrop.objects.create(
        crop_name="Tomato",
        category="Vegetables",
        crop_type="Semi-Perennial",
        description="Fresh tomatoes",
        is_active=True
    )


@pytest.fixture
def crop(db, farmer_user, master_crop):
    """Create a test crop listing"""
    from datetime import date, timedelta
    return Crop.objects.create(
        farmer=farmer_user,
        master_crop=master_crop,
        quantity=100.0,
        unit='kg',
        price_per_unit=50.0,
        location='Dhaka',
        harvest_date=date.today(),
        availability_date=date.today(),
        quality_grade='A',
        is_available=True
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='adminpass123',
        role='admin'
    )
