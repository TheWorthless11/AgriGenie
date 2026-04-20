from datetime import date, timedelta

from django.test import TestCase

from admin_panel.models import MasterCrop
from farmer.forms import CropForm
from farmer.models import Crop
from users.models import CustomUser


class CropFormAndModelTests(TestCase):
    def setUp(self):
        self.farmer = CustomUser.objects.create_user(
            username='farmer_one',
            role='farmer',
            password='StrongPass123',
        )
        self.active_crop = MasterCrop.objects.create(
            crop_name='Tomato',
            category='vegetables',
            is_active=True,
        )
        self.inactive_crop = MasterCrop.objects.create(
            crop_name='Inactive Rice',
            category='grains',
            is_active=False,
        )

    def _create_listing(self, **overrides):
        defaults = {
            'farmer': self.farmer,
            'master_crop': self.active_crop,
            'quantity': 10,
            'unit': 'kg',
            'price_per_unit': 50,
            'location': 'Dhaka',
            'harvest_date': date.today(),
            'availability_date': date.today() + timedelta(days=1),
            'quality_grade': 'A',
            'area_size': 1,
            'area_unit': 'm2',
        }
        defaults.update(overrides)
        return Crop.objects.create(**defaults)

    def test_crop_form_shows_only_active_master_crops(self):
        form = CropForm()
        queryset = form.fields['master_crop'].queryset

        self.assertIn(self.active_crop, queryset)
        self.assertNotIn(self.inactive_crop, queryset)

    def test_deduct_and_restore_quantity_updates_stock_fields(self):
        listing = self._create_listing(quantity=7)

        listing.deduct_quantity(3)
        listing.refresh_from_db()
        self.assertEqual(listing.quantity, 4)
        self.assertTrue(listing.is_available)
        self.assertIsNone(listing.out_of_stock_since)

        listing.deduct_quantity(10)
        listing.refresh_from_db()
        self.assertEqual(listing.quantity, 0)
        self.assertFalse(listing.is_available)
        self.assertIsNotNone(listing.out_of_stock_since)

        listing.restore_quantity(2)
        listing.refresh_from_db()
        self.assertEqual(listing.quantity, 2)
        self.assertTrue(listing.is_available)
        self.assertIsNone(listing.out_of_stock_since)

    def test_area_size_m2_converts_area_units(self):
        listing = self._create_listing(area_size=1.0, area_unit='acre')
        self.assertAlmostEqual(listing.area_size_m2, 4046.86, places=2)
