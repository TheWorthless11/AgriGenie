"""
Unit tests for Django models across the AgriGenie application.
Tests cover: CustomUser, FarmerProfile, BuyerProfile, Crop, Order, ChatRoom, etc.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from users.models import FarmerProfile, BuyerProfile
from farmer.models import Crop, Order
from buyer.models import PurchaseRequest, WishlistItem, SavedCrop
from chat.models import ChatRoom, ChatMessage
from admin_panel.models import MasterCrop

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCustomUserModel:
    """Test CustomUser model functionality"""
    
    def test_create_farmer_user(self):
        """Test creating a farmer user"""
        user = User.objects.create_user(
            username='farmer1',
            email='farmer1@test.com',
            password='test123',
            role='farmer'
        )
        assert user.username == 'farmer1'
        assert user.role == 'farmer'
        assert user.check_password('test123')
    
    def test_create_buyer_user(self):
        """Test creating a buyer user"""
        user = User.objects.create_user(
            username='buyer1',
            email='buyer1@test.com',
            password='test123',
            role='buyer'
        )
        assert user.username == 'buyer1'
        assert user.role == 'buyer'
    
    def test_create_superuser(self):
        """Test creating a superuser (admin)"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.role == 'admin'
    
    def test_pin_authentication(self, farmer_user):
        """Test PIN hashing and verification"""
        farmer_user.set_pin('1234')
        farmer_user.save()
        
        assert farmer_user.check_pin('1234')
        assert not farmer_user.check_pin('5678')
    
    def test_full_location(self, farmer_user):
        """Test get_full_location method"""
        farmer_user.district = 'Dhaka'
        farmer_user.upazila = 'Sadar'
        location = farmer_user.get_full_location()
        
        assert 'Sadar' in location
        assert 'Dhaka' in location
    
    def test_user_str_representation(self, farmer_user):
        """Test string representation of user"""
        assert 'testfarmer' in str(farmer_user)
        assert 'Farmer' in str(farmer_user)
    
    def test_user_blocking(self, buyer_user):
        """Test admin blocking functionality"""
        buyer_user.is_blocked_by_admin = True
        buyer_user.blocked_reason = 'Fraudulent activity'
        buyer_user.save()
        
        assert buyer_user.is_blocked_by_admin
        assert buyer_user.blocked_reason == 'Fraudulent activity'


class TestFarmerProfile:
    """Test FarmerProfile model"""
    
    def test_create_farmer_profile(self, farmer_user):
        """Test creating a farmer profile"""
        profile = FarmerProfile.objects.create(
            user=farmer_user,
            farm_name="Test Farm",
            farm_size=5.0,
            farm_location="Dhaka",
            soil_type="Clay",
            experience_years=10,
            registration_number="FAR-001"
        )
        assert profile.farm_name == "Test Farm"
        assert profile.farm_size == 5.0
        assert not profile.is_approved
    
    def test_unique_registration_number(self, farmer_user, db):
        """Test registration number uniqueness"""
        FarmerProfile.objects.create(
            user=farmer_user,
            farm_name="Farm 1",
            farm_size=5.0,
            farm_location="Dhaka",
            soil_type="Clay",
            experience_years=5,
            registration_number="FAR-UNIQUE-001"
        )
        
        farmer_user2 = User.objects.create_user(
            username='farmer2',
            email='farmer2@test.com',
            password='test123',
            role='farmer'
        )
        
        with pytest.raises(IntegrityError):
            FarmerProfile.objects.create(
                user=farmer_user2,
                farm_name="Farm 2",
                farm_size=3.0,
                farm_location="Dhaka",
                soil_type="Loam",
                experience_years=3,
                registration_number="FAR-UNIQUE-001"  # Duplicate
            )
    
    def test_farmer_rating(self, farmer_profile):
        """Test farmer rating validation"""
        farmer_profile.rating = 4.5
        farmer_profile.save()
        
        assert farmer_profile.rating == 4.5
        
        # Test rating bounds
        farmer_profile.rating = 0
        farmer_profile.save()
        assert farmer_profile.rating == 0


class TestBuyerProfile:
    """Test BuyerProfile model"""
    
    def test_create_buyer_profile(self, buyer_user):
        """Test creating a buyer profile"""
        profile = BuyerProfile.objects.create(
            user=buyer_user,
            company_name="Agro Corp",
            business_type="Wholesale",
            registration_number="BUY-001"
        )
        assert profile.company_name == "Agro Corp"
        assert profile.business_type == "Wholesale"
    
    def test_buyer_profile_str(self, buyer_profile):
        """Test buyer profile string representation"""
        assert 'Agro Corp' in str(buyer_profile)


class TestMasterCrop:
    """Test MasterCrop model"""
    
    def test_create_master_crop(self):
        """Test creating a master crop"""
        crop = MasterCrop.objects.create(
            crop_name="Rice",
            category="Grains",
            crop_type="Annual",
            description="White rice",
            is_active=True
        )
        assert crop.crop_name == "Rice"
        assert crop.is_active
    
    def test_master_crop_str(self, master_crop):
        """Test master crop string representation"""
        assert 'Tomato' in str(master_crop)


class TestCrop:
    """Test Crop listing model"""
    
    def test_create_crop_listing(self, crop):
        """Test creating a crop listing"""
        assert crop.farmer.username == 'testfarmer'
        assert crop.quantity == 100.0
        assert crop.unit == 'kg'
        assert crop.price_per_unit == 50.0
        assert crop.is_available
    
    def test_crop_string_representation(self, crop):
        """Test crop string representation"""
        assert 'Tomato' in str(crop)
        assert 'testfarmer' in str(crop)
    
    def test_crop_availability(self, crop):
        """Test crop availability status"""
        assert crop.is_available
        
        crop.is_available = False
        crop.save()
        assert not crop.is_available
    
    def test_crop_quantity_validation(self, crop):
        """Test quantity cannot be negative"""
        crop.quantity = -10
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            crop.full_clean()
    
    def test_crop_price_validation(self, crop):
        """Test price cannot be negative"""
        crop.price_per_unit = -5
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            crop.full_clean()
    
    def test_crop_quality_grades(self, farmer_user, master_crop):
        """Test different quality grades"""
        grades = ['A', 'B', 'C']
        
        for grade in grades:
            crop = Crop.objects.create(
                farmer=farmer_user,
                master_crop=master_crop,
                quantity=50,
                unit='kg',
                price_per_unit=30,
                location='Dhaka',
                harvest_date=date.today(),
                availability_date=date.today(),
                quality_grade=grade
            )
            assert crop.quality_grade == grade


class TestOrder:
    """Test Order model"""
    
    def test_create_order(self, crop, buyer_user):
        """Test creating an order"""
        order = Order.objects.create(
            crop=crop,
            farmer=crop.farmer,
            buyer=buyer_user,
            quantity=50,
            total_price=50 * crop.price_per_unit,
            order_date=date.today(),
            status='pending'
        )
        assert order.crop == crop
        assert order.buyer == buyer_user
        assert order.quantity == 50
        assert order.status == 'pending'
    
    def test_order_status_workflow(self, crop, buyer_user):
        """Test order status transitions"""
        order = Order.objects.create(
            crop=crop,
            farmer=crop.farmer,
            buyer=buyer_user,
            quantity=25,
            total_price=25 * crop.price_per_unit,
            order_date=date.today(),
            status='pending'
        )
        
        # Transition through statuses
        statuses = ['pending', 'confirmed', 'delivered', 'completed']
        for status in statuses:
            order.status = status
            order.save()
            assert order.status == status


class TestPurchaseRequest:
    """Test PurchaseRequest model"""
    
    def test_create_purchase_request(self, crop, buyer_user):
        """Test creating a purchase request"""
        pr = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=30,
            preferred_price=45,
            message="Interested in your tomatoes"
        )
        assert pr.crop == crop
        assert pr.buyer == buyer_user
        assert pr.status == 'pending'
    
    def test_purchase_request_status(self, crop, buyer_user):
        """Test purchase request status transitions"""
        pr = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=20
        )
        
        statuses = ['pending', 'accepted', 'rejected', 'completed']
        for status in statuses:
            pr.status = status
            pr.save()
            assert pr.status == status


class TestWishlistItem:
    """Test WishlistItem model"""
    
    def test_add_to_wishlist(self, crop, buyer_user):
        """Test adding crop to wishlist"""
        wishlist = WishlistItem.objects.create(
            buyer=buyer_user,
            crop=crop
        )
        assert wishlist.crop == crop
        assert wishlist.buyer == buyer_user
    
    def test_unique_wishlist_entry(self, crop, buyer_user):
        """Test cannot add same crop twice to wishlist"""
        WishlistItem.objects.create(
            buyer=buyer_user,
            crop=crop
        )
        
        with pytest.raises(IntegrityError):
            WishlistItem.objects.create(
                buyer=buyer_user,
                crop=crop
            )


class TestSavedCrop:
    """Test SavedCrop model"""
    
    def test_save_crop(self, crop, buyer_user):
        """Test saving a crop"""
        saved = SavedCrop.objects.create(
            buyer=buyer_user,
            crop=crop
        )
        assert saved.crop == crop
        assert saved.buyer == buyer_user
    
    def test_unique_saved_crop(self, crop, buyer_user):
        """Test cannot save same crop twice"""
        SavedCrop.objects.create(
            buyer=buyer_user,
            crop=crop
        )
        
        with pytest.raises(IntegrityError):
            SavedCrop.objects.create(
                buyer=buyer_user,
                crop=crop
            )


class TestChatRoom:
    """Test ChatRoom model"""
    
    def test_create_chat_room(self, farmer_user, buyer_user, crop):
        """Test creating a chat room"""
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user,
            crop=crop
        )
        assert room.farmer == farmer_user
        assert room.buyer == buyer_user
        assert room.crop == crop
    
    def test_chat_room_room_name(self, farmer_user, buyer_user):
        """Test room name generation"""
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user
        )
        assert 'chat_' in room.room_name
        assert str(room.id) in room.room_name
    
    def test_get_other_user(self, farmer_user, buyer_user):
        """Test getting other participant"""
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user
        )
        
        other = room.get_other_user(farmer_user)
        assert other == buyer_user
        
        other = room.get_other_user(buyer_user)
        assert other == farmer_user


class TestChatMessage:
    """Test ChatMessage model"""
    
    def test_create_message(self, farmer_user, buyer_user):
        """Test creating a chat message"""
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user
        )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=farmer_user,
            content="Hello, interested in tomatoes?"
        )
        assert message.room == room
        assert message.sender == farmer_user
        assert not message.is_read
    
    def test_message_read_status(self, farmer_user, buyer_user):
        """Test marking message as read"""
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user
        )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=farmer_user,
            content="Test message"
        )
        
        assert not message.is_read
        message.is_read = True
        message.save()
        assert message.is_read
