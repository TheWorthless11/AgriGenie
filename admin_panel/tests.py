from django.test import TestCase

from admin_panel.models import AdminSettings, MasterCrop
from users.models import CustomUser


class AdminPanelModelTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin_tester',
            email='admin_tester@example.com',
            password='StrongPass123',
        )

    def test_get_solo_returns_singleton_settings_instance(self):
        first = AdminSettings.get_solo()
        second = AdminSettings.get_solo()

        self.assertEqual(first.pk, 1)
        self.assertEqual(first.pk, second.pk)

    def test_reset_to_defaults_restores_expected_values(self):
        settings_obj = AdminSettings.get_solo()
        settings_obj.site_name = 'Custom Name'
        settings_obj.password_min_length = 12
        settings_obj.maintenance_mode = True
        settings_obj.ai_api_key = 'abc123'

        settings_obj.reset_to_defaults()

        self.assertEqual(settings_obj.site_name, 'AgriGenie')
        self.assertEqual(settings_obj.password_min_length, 8)
        self.assertFalse(settings_obj.maintenance_mode)
        self.assertEqual(settings_obj.ai_api_key, '')

    def test_master_crop_string_representation_contains_crop_name(self):
        crop = MasterCrop.objects.create(
            crop_name='Tomato',
            category='vegetables',
            created_by=self.admin_user,
        )

        self.assertIn('Tomato', str(crop))
