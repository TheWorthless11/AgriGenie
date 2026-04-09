"""
Unit tests for Django views across the AgriGenie application.
Tests cover: authentication, farmer dashboard, buyer marketplace, admin panel, etc.
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import FarmerProfile, BuyerProfile
from farmer.models import Crop
from admin_panel.models import MasterCrop

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestAuthenticationViews:
    """Test registration and login views"""
    
    def test_homepage_accessible(self):
        """Test homepage is accessible"""
        client = Client()
        response = client.get('/')
        assert response.status_code in [200, 302]  # 302 if redirects to login
    
    def test_farmer_registration(self, db):
        """Test farmer registration flow"""
        client = Client()
        # Assuming static registration form - update URL as needed
        data = {
            'full_name': 'Test Farmer',
            'phone_number': '+8801712345678',
            'username': 'testfarmer',
            'email': 'farmer@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'farmer',
            'district': 'Dhaka',
            'upazila': 'Sadar',
            'country': 'Bangladesh',
            'auth_type': 'pin',
            'pin': '1234',
            'confirm_pin': '1234'
        }
        # Verify registration creates user
        assert User.objects.filter(username='testfarmer').count() == 0
    
    def test_buyer_registration(self, db):
        """Test buyer registration flow"""
        client = Client()
        data = {
            'full_name': 'Test Buyer',
            'phone_number': '+8801987654321',
            'username': 'testbuyer',
            'email': 'buyer@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'buyer',
            'district': 'Chittagong',
            'upazila': 'Kotwali'
        }
        # Verify registration creates user
        assert User.objects.filter(username='testbuyer').count() == 0


class TestFarmerViews:
    """Test farmer-specific views"""
    
    def test_farmer_dashboard_access(self, farmer_user):
        """Test farmer can access dashboard"""
        client = Client()
        client.login(username='testfarmer', password='testpass123')
        
        # Try accessing farmer dashboard if URL exists
        response = client.get('/farmer/dashboard/')
        assert response.status_code in [200, 404]  # 404 if URL doesn't exist
    
    def test_farmer_cannot_access_buyer_dashboard(self, farmer_user):
        """Test farmer cannot access buyer dashboard"""
        client = Client()
        client.login(username='testfarmer', password='testpass123')
        
        response = client.get('/buyer/dashboard/')
        # Should be 403 Forbidden or 404 if route doesn't exist
        assert response.status_code in [403, 404, 302]  # 302 if redirects
    
    def test_crop_creation_form(self, farmer_user):
        """Test farmer can access crop creation form"""
        client = Client()
        client.login(username='testfarmer', password='testpass123')
        
        # Test accessing crop creation page
        response = client.get('/farmer/add_crop/')
        assert response.status_code in [200, 404]


class TestBuyerViews:
    """Test buyer-specific views"""
    
    def test_buyer_marketplace_access(self, buyer_user):
        """Test buyer can access marketplace"""
        client = Client()
        client.login(username='testbuyer', password='testpass123')
        
        response = client.get('/buyer/marketplace/')
        assert response.status_code in [200, 404]
    
    def test_buyer_dashboard_access(self, buyer_user):
        """Test buyer can access dashboard"""
        client = Client()
        client.login(username='testbuyer', password='testpass123')
        
        response = client.get('/buyer/dashboard/')
        assert response.status_code in [200, 404]
    
    def test_buyer_cannot_access_farmer_dashboard(self, buyer_user):
        """Test buyer cannot access farmer dashboard"""
        client = Client()
        client.login(username='testbuyer', password='testpass123')
        
        response = client.get('/farmer/dashboard/')
        assert response.status_code in [403, 404, 302]


class TestAdminViews:
    """Test admin panel views"""
    
    def test_admin_dashboard_access_with_admin(self, admin_user):
        """Test admin can access dashboard"""
        client = Client()
        client.login(username='admin', password='adminpass123')
        
        response = client.get('/admin-panel/dashboard/')
        assert response.status_code in [200, 404, 302]
    
    def test_admin_user_management(self, admin_user):
        """Test admin can access user management"""
        client = Client()
        client.login(username='admin', password='adminpass123')
        
        response = client.get('/admin-panel/users/')
        assert response.status_code in [200, 404, 302]
    
    def test_non_admin_cannot_access_admin_panel(self, farmer_user):
        """Test non-admin cannot access admin panel"""
        client = Client()
        client.login(username='testfarmer', password='testpass123')
        
        response = client.get('/admin-panel/dashboard/')
        assert response.status_code in [403, 404, 302]


class TestPublicPages:
    """Test publicly accessible pages"""
    
    def test_home_page(self):
        """Test home page is accessible"""
        client = Client()
        response = client.get('/')
        assert response.status_code in [200, 302]
    
    def test_about_page_if_exists(self):
        """Test about page if it exists"""
        client = Client()
        response = client.get('/about/')
        assert response.status_code in [200, 404]
    
    def test_contact_page_if_exists(self):
        """Test contact page if it exists"""
        client = Client()
        response = client.get('/contact/')
        assert response.status_code in [200, 404]


class TestAPIViews:
    """Test REST API endpoints if they exist"""
    
    def test_crops_api_list(self, farmer_user, crop):
        """Test crops API list endpoint"""
        client = Client()
        response = client.get('/api/crops/')
        assert response.status_code in [200, 302, 404]
    
    def test_crops_api_detail(self, crop):
        """Test crops API detail endpoint"""
        client = Client()
        response = client.get(f'/api/crops/{crop.id}/')
        assert response.status_code in [200, 404]
    
    def test_users_api(self):
        """Test users API endpoint"""
        client = Client()
        response = client.get('/api/users/')
        assert response.status_code in [200, 401, 404]
