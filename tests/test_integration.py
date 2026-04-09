"""
Integration tests for AgriGenie workflows.
Tests complete user journeys: registration → crop listing → purchase → messaging
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import Client
from users.models import FarmerProfile, BuyerProfile
from farmer.models import Crop, Order
from buyer.models import PurchaseRequest, WishlistItem, SavedCrop
from chat.models import ChatRoom, ChatMessage
from admin_panel.models import MasterCrop

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserRegistrationWorkflow:
    """Integration test for complete user registration workflow"""
    
    def test_farmer_registration_and_approval_workflow(self):
        """Test complete farmer registration and approval process"""
        # Step 1: Farmer registers
        farmer = User.objects.create_user(
            username='new_farmer',
            email='newfarmer@test.com',
            password='testpass123',
            role='farmer',
            phone_number='+8801712345678',
            district='Dhaka',
            upazila='Sadar'
        )
        assert farmer.role == 'farmer'
        assert not farmer.is_verified
        
        # Step 2: Create farmer profile with NID verification
        profile = FarmerProfile.objects.create(
            user=farmer,
            farm_name="New Farm",
            farm_size=3.0,
            farm_location="Dhaka",
            soil_type="Clay",
            experience_years=5,
            registration_number="FAR-NEW-001",
            is_approved=False
        )
        assert not profile.is_approved
        
        # Step 3: Admin approves farmer
        profile.is_approved = True
        profile.save()
        assert profile.is_approved
        
        # Step 4: Farmer can now post crops
        assert farmer.is_staff == False  # Regular user
        assert farmer.role == 'farmer'
    
    def test_buyer_registration_and_verification_workflow(self):
        """Test complete buyer registration and verification process"""
        # Step 1: Buyer registers
        buyer = User.objects.create_user(
            username='new_buyer',
            email='newbuyer@test.com',
            password='testpass123',
            role='buyer',
            phone_number='+8801987654321',
            district='Chittagong'
        )
        assert buyer.role == 'buyer'
        
        # Step 2: Create buyer profile
        profile = BuyerProfile.objects.create(
            user=buyer,
            company_name="New Corp",
            business_type="Wholesale",
            registration_number="BUY-NEW-001",
            is_approved=False
        )
        assert not profile.is_approved
        
        # Step 3: Admin approves buyer
        profile.is_approved = True
        profile.save()
        assert profile.is_approved


class TestCropListingAndSearchWorkflow:
    """Integration test for crop listing and search"""
    
    def test_farmer_posts_crop_buyer_searches(self, farmer_user, buyer_user, master_crop):
        """Test farmer posts crop and buyer searches"""
        # Step 1: Farmer creates crop listing
        crop = Crop.objects.create(
            farmer=farmer_user,
            master_crop=master_crop,
            quantity=200,
            unit='kg',
            price_per_unit=50,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today(),
            quality_grade='A',
            is_available=True
        )
        assert crop.is_available
        assert crop.quantity == 200
        
        # Step 2: Verify crop can be found
        found_crop = Crop.objects.get(id=crop.id)
        assert found_crop.farmer == farmer_user
        assert found_crop.master_crop == master_crop
        
        # Step 3: Verify buyer can view crop
        buyer_crops = Crop.objects.filter(is_available=True)
        assert crop in buyer_crops
    
    def test_multiple_crops_by_same_farmer(self, farmer_user, master_crop):
        """Test farmer can post multiple crops"""
        crops = []
        for i in range(3):
            crop = Crop.objects.create(
                farmer=farmer_user,
                master_crop=master_crop,
                quantity=100 + (i * 50),
                unit='kg',
                price_per_unit=50 + (i * 5),
                location='Dhaka',
                harvest_date=date.today(),
                availability_date=date.today(),
                quality_grade='A'
            )
            crops.append(crop)
        
        # Verify all crops belong to farmer
        farmer_crops = Crop.objects.filter(farmer=farmer_user)
        assert farmer_crops.count() == 3
        
        # Verify each crop is unique
        prices = [c.price_per_unit for c in farmer_crops]
        assert len(set(prices)) == 3


class TestPurchaseWorkflow:
    """Integration test for purchase request workflow"""
    
    def test_complete_purchase_request_workflow(self, crop, buyer_user):
        """Test complete purchase request workflow"""
        # Step 1: Buyer creates purchase request
        pr = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=100,
            preferred_price=48,
            message="Interested in bulk purchase"
        )
        assert pr.status == 'pending'
        
        # Step 2: Farmer accepts request
        pr.status = 'accepted'
        pr.save()
        assert pr.status == 'accepted'
        
        # Step 3: Create order from purchase request
        order = Order.objects.create(
            crop=crop,
            farmer=crop.farmer,
            buyer=buyer_user,
            quantity=100,
            total_price=100 * crop.price_per_unit,
            order_date=date.today(),
            status='confirmed'
        )
        assert order.quantity == pr.quantity_required
        
        # Step 4: Complete order
        order.status = 'completed'
        order.save()
        assert order.status == 'completed'
    
    def test_purchase_request_rejection_workflow(self, crop, buyer_user):
        """Test purchase request rejection workflow"""
        pr = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=500,  # More than available
            preferred_price=30  # Below asking price
        )
        
        # Farmer rejects request
        pr.status = 'rejected'
        pr.save()
        assert pr.status == 'rejected'
        
        # Buyer can make new request
        pr2 = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=100,
            preferred_price=50
        )
        assert pr2.status == 'pending'


class TestWishlistAndSavingWorkflow:
    """Integration test for wishlist and saved crops"""
    
    def test_buyer_manages_wishlist(self, crop, buyer_user):
        """Test buyer adds/removes crops from wishlist"""
        # Step 1: Add to wishlist
        wishlist = WishlistItem.objects.create(
            buyer=buyer_user,
            crop=crop
        )
        assert wishlist.crop == crop
        
        # Step 2: Verify in wishlist
        buyer_wishlist = WishlistItem.objects.filter(buyer=buyer_user)
        assert crop in [w.crop for w in buyer_wishlist]
        
        # Step 3: Remove from wishlist
        wishlist.delete()
        
        # Step 4: Verify removed
        buyer_wishlist = WishlistItem.objects.filter(buyer=buyer_user)
        assert crop not in [w.crop for w in buyer_wishlist]
    
    def test_buyer_saves_crops(self, buyer_user, farmer_user, master_crop):
        """Test buyer saves crops for later"""
        # Create multiple crops
        crop1 = Crop.objects.create(
            farmer=farmer_user,
            master_crop=master_crop,
            quantity=100,
            unit='kg',
            price_per_unit=50,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today()
        )
        crop2 = Crop.objects.create(
            farmer=farmer_user,
            master_crop=master_crop,
            quantity=150,
            unit='kg',
            price_per_unit=60,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today()
        )
        
        # Save both crops
        SavedCrop.objects.create(buyer=buyer_user, crop=crop1)
        SavedCrop.objects.create(buyer=buyer_user, crop=crop2)
        
        # Verify both saved
        saved = SavedCrop.objects.filter(buyer=buyer_user)
        assert saved.count() == 2
        assert crop1 in [s.crop for s in saved]
        assert crop2 in [s.crop for s in saved]


class TestMessagingWorkflow:
    """Integration test for real-time messaging between users"""
    
    def test_chat_creation_workflow(self, farmer_user, buyer_user, crop):
        """Test creating and managing chat rooms"""
        # Step 1: Create chat room
        room = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer_user,
            crop=crop
        )
        assert room.farmer == farmer_user
        assert room.buyer == buyer_user
        
        # Step 2: Farmer sends first message
        msg1 = ChatMessage.objects.create(
            room=room,
            sender=farmer_user,
            content="Hello! Interested in our tomatoes?"
        )
        assert msg1.sender == farmer_user
        assert not msg1.is_read
        
        # Step 3: Buyer reads and replies
        msg1.is_read = True
        msg1.save()
        
        msg2 = ChatMessage.objects.create(
            room=room,
            sender=buyer_user,
            content="Yes! What's the best price for bulk?"
        )
        assert msg2.sender == buyer_user
        
        # Step 4: Verify conversation
        messages = ChatMessage.objects.filter(room=room)
        assert messages.count() == 2
    
    def test_multiple_chat_rooms(self, farmer_user, buyer_user, 
                                  master_crop):
        """Test farmer has multiple chat rooms with different buyers"""
        # Create two buyer users
        buyer1 = User.objects.create_user(
            username='buyer1',
            email='buyer1@test.com',
            password='test123',
            role='buyer'
        )
        buyer2 = User.objects.create_user(
            username='buyer2',
            email='buyer2@test.com',
            password='test123',
            role='buyer'
        )
        
        # Create two crops by farmer
        crop1 = Crop.objects.create(
            farmer=farmer_user,
            master_crop=master_crop,
            quantity=100,
            unit='kg',
            price_per_unit=50,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today()
        )
        crop2 = Crop.objects.create(
            farmer=farmer_user,
            master_crop=master_crop,
            quantity=200,
            unit='kg',
            price_per_unit=55,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today()
        )
        
        # Create chat rooms
        room1 = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer1,
            crop=crop1
        )
        room2 = ChatRoom.objects.create(
            farmer=farmer_user,
            buyer=buyer2,
            crop=crop2
        )
        
        # Verify separate conversations
        farmer_chats = ChatRoom.objects.filter(farmer=farmer_user)
        assert farmer_chats.count() == 2


class TestOrderLifecycleWorkflow:
    """Integration test for complete order lifecycle"""
    
    def test_order_from_creation_to_completion(self, crop, buyer_user):
        """Test complete order lifecycle"""
        # Step 1: Create purchase request
        pr = PurchaseRequest.objects.create(
            buyer=buyer_user,
            crop=crop,
            quantity_required=50,
            preferred_price=48
        )
        
        # Step 2: Create order
        order = Order.objects.create(
            crop=crop,
            farmer=crop.farmer,
            buyer=buyer_user,
            quantity=50,
            total_price=50 * crop.price_per_unit,
            order_date=date.today(),
            status='pending'
        )
        assert order.status == 'pending'
        
        # Step 3: Confirm order
        order.status = 'confirmed'
        order.save()
        assert order.status == 'confirmed'
        
        # Step 4: Deliver order
        order.status = 'delivered'
        order.save()
        assert order.status == 'delivered'
        
        # Step 5: Complete order
        order.status = 'completed'
        order.save()
        assert order.status == 'completed'
        
        # Verify final state
        final_order = Order.objects.get(id=order.id)
        assert final_order.status == 'completed'
        assert final_order.quantity == 50


class TestCropAvailabilityWorkflow:
    """Integration test for crop availability changes"""
    
    def test_crop_becomes_unavailable(self, crop, buyer_user):
        """Test crop availability transitions"""
        initial_state = crop.is_available
        assert initial_state
        
        # Buyer creates purchase request for full quantity
        order = Order.objects.create(
            crop=crop,
            farmer=crop.farmer,
            buyer=buyer_user,
            quantity=crop.quantity,
            total_price=crop.quantity * crop.price_per_unit,
            order_date=date.today()
        )
        
        # Farmer marks crop as unavailable
        crop.is_available = False
        crop.save()
        assert not crop.is_available
        
        # Verify other buyers cannot see crop
        available_crops = Crop.objects.filter(is_available=True)
        assert crop not in available_crops
    
    def test_crop_becomes_available_again(self, crop):
        """Test crop availability recovery"""
        crop.is_available = False
        crop.save()
        
        # Admin re-lists crop
        crop.is_available = True
        crop.save()
        
        available_crops = Crop.objects.filter(is_available=True)
        assert crop in available_crops
