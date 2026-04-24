from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from farmer.models import Crop, Order
from payment.models import Payment, PaymentGatewayConfig
from datetime import datetime, timedelta

User = get_user_model()


class PaymentTests(TestCase):
    """Test payment functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.buyer = User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpass123',
            role='buyer'
        )
        
        self.farmer = User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            role='farmer'
        )
        
        # Create crop
        self.crop = Crop.objects.create(
            farmer=self.farmer,
            crop_name='Test Crop',
            quantity=100,
            unit='kg',
            price_per_unit=50,
            location='Test Location',
            harvest_date='2026-05-01',
            quality_grade='A'
        )
        
        # Create order
        self.order = Order.objects.create(
            crop=self.crop,
            buyer=self.buyer,
            farmer=self.farmer,
            quantity=10,
            total_price=500,
            status='accepted',
            delivery_date='2026-06-01'
        )
        
        self.client = Client()
    
    def test_choose_payment_method_view_requires_login(self):
        """Test that payment method view requires login"""
        response = self.client.get(reverse('payment:choose_payment_method', args=[self.order.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_payment_method_form_cod(self):
        """Test selecting COD payment method"""
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.post(
            reverse('payment:choose_payment_method', args=[self.order.id]),
            {'payment_method': 'cod'}
        )
        self.assertEqual(response.status_code, 302)
        
        # Check payment was created
        payment = Payment.objects.filter(order=self.order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, 'cod')
        self.assertEqual(payment.status, 'completed')
    
    def test_payment_creation_cod_amounts(self):
        """Test that COD payment amounts are calculated correctly"""
        self.client.login(username='testbuyer', password='testpass123')
        self.client.post(
            reverse('payment:choose_payment_method', args=[self.order.id]),
            {'payment_method': 'cod'}
        )
        
        payment = Payment.objects.filter(order=self.order).first()
        self.assertAlmostEqual(payment.upfront_amount, 100)  # 20% of 500
        self.assertAlmostEqual(payment.remaining_amount, 400)  # 80% of 500
        self.assertAlmostEqual(payment.paid_amount, 100)
    
    def test_payment_for_non_accepted_order(self):
        """Test payment not allowed for non-accepted orders"""
        pending_order = Order.objects.create(
            crop=self.crop,
            buyer=self.buyer,
            farmer=self.farmer,
            quantity=5,
            total_price=250,
            status='pending',
            delivery_date='2026-06-01'
        )
        
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(
            reverse('payment:choose_payment_method', args=[pending_order.id])
        )
        
        self.assertEqual(response.status_code, 302)
    
    def test_payment_details_view_authorization(self):
        """Test payment details view authorization"""
        # Create payment
        payment = Payment.objects.create(
            order=self.order,
            payment_method='cod',
            total_amount=500,
            status='completed'
        )
        
        # Test buyer can view
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('payment:payment_details', args=[payment.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test unauthorized user cannot view
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='testpass123',
            role='buyer'
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.get(reverse('payment:payment_details', args=[payment.id]))
        self.assertEqual(response.status_code, 302)  # Redirect (denied)
