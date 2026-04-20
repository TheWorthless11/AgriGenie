from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from admin_panel.models import MasterCrop
from buyer.models import WishlistItem
from farmer.models import Crop
from marketplace.models import Review
from users.models import CustomUser


class MarketplaceFlowTests(TestCase):
    def setUp(self):
        self.buyer = CustomUser.objects.create_user(
            username='buyer_market',
            role='buyer',
            email='buyer_market@example.com',
            password='StrongPass123',
        )
        self.farmer = CustomUser.objects.create_user(
            username='farmer_market',
            role='farmer',
            password='StrongPass123',
        )
        master_crop = MasterCrop.objects.create(
            crop_name='Onion',
            category='vegetables',
            is_active=True,
        )
        self.crop = Crop.objects.create(
            farmer=self.farmer,
            master_crop=master_crop,
            quantity=15,
            unit='kg',
            price_per_unit=35,
            location='Dhaka',
            harvest_date=date.today(),
            availability_date=date.today() + timedelta(days=1),
            quality_grade='B',
        )

    def test_add_to_wishlist_requires_login(self):
        response = self.client.get(reverse('add_to_wishlist', args=[self.crop.id]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_add_to_wishlist_creates_item_for_logged_in_user(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse('add_to_wishlist', args=[self.crop.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(WishlistItem.objects.filter(buyer=self.buyer, crop=self.crop).exists())

    def test_save_crop_endpoint_toggles_saved_state(self):
        self.client.force_login(self.buyer)
        url = reverse('save_crop', args=[self.crop.id]) + f"?next={reverse('crop_listing', args=[self.crop.id])}"

        self.client.get(url)
        self.assertEqual(self.buyer.saved_crops.filter(crop=self.crop).count(), 1)

        self.client.get(url)
        self.assertEqual(self.buyer.saved_crops.filter(crop=self.crop).count(), 0)

    def test_review_is_unique_for_same_reviewer_and_crop(self):
        Review.objects.create(
            crop=self.crop,
            reviewer=self.buyer,
            rating=5,
            title='Excellent',
            review_text='Fresh and high quality crop.',
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    crop=self.crop,
                    reviewer=self.buyer,
                    rating=4,
                    title='Duplicate',
                    review_text='Should fail due to unique constraint.',
                )
