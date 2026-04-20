from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from admin_panel.models import MasterCrop
from buyer.models import SavedCrop, WishlistItem
from farmer.models import Crop
from users.models import CustomUser


class BuyerModelAndAccessTests(TestCase):
    def setUp(self):
        self.buyer = CustomUser.objects.create_user(
            username='buyer_one',
            role='buyer',
            email='buyer_one@example.com',
            password='StrongPass123',
        )
        self.farmer = CustomUser.objects.create_user(
            username='farmer_for_buyer_tests',
            role='farmer',
            password='StrongPass123',
        )
        master_crop = MasterCrop.objects.create(
            crop_name='Potato',
            category='vegetables',
            is_active=True,
        )
        self.crop = Crop.objects.create(
            farmer=self.farmer,
            master_crop=master_crop,
            quantity=20,
            unit='kg',
            price_per_unit=40,
            location='Khulna',
            harvest_date=date.today(),
            availability_date=date.today() + timedelta(days=1),
            quality_grade='A',
        )

    def test_wishlist_item_is_unique_per_buyer_and_crop(self):
        WishlistItem.objects.create(buyer=self.buyer, crop=self.crop)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WishlistItem.objects.create(buyer=self.buyer, crop=self.crop)

    def test_saved_crop_is_unique_per_buyer_and_crop(self):
        SavedCrop.objects.create(buyer=self.buyer, crop=self.crop)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SavedCrop.objects.create(buyer=self.buyer, crop=self.crop)

    def test_buyer_routes_require_authentication(self):
        response = self.client.get(reverse('buyer_orders'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_marketplace_view_rejects_non_buyer_user(self):
        self.client.force_login(self.farmer)

        response = self.client.get(reverse('marketplace'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)
