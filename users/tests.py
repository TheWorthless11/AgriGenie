from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from users.forms import DynamicRegistrationForm
from users.models import CustomUser, OTPVerification, PasswordResetToken


class CustomUserPinTests(TestCase):
	def test_set_and_check_pin(self):
		user = CustomUser.objects.create_user(
			username='farmer_pin',
			role='farmer',
			password='unused-password',
		)

		user.set_pin('1234')
		user.save()

		self.assertNotEqual(user.pin_hash, '1234')
		self.assertTrue(user.check_pin('1234'))
		self.assertFalse(user.check_pin('9999'))


class OTPVerificationTests(TestCase):
	def test_generate_otp_replaces_previous_unverified_record(self):
		old_otp = OTPVerification.objects.create(
			phone_number='+8801710000001',
			otp_code='111111',
			expires_at=timezone.now() + timedelta(minutes=10),
		)

		new_otp = OTPVerification.generate_otp('+8801710000001')

		self.assertFalse(OTPVerification.objects.filter(id=old_otp.id).exists())
		self.assertEqual(OTPVerification.objects.filter(phone_number='+8801710000001').count(), 1)
		self.assertEqual(len(new_otp.otp_code), 6)

	def test_can_send_otp_blocks_requests_within_one_minute(self):
		OTPVerification.objects.create(
			phone_number='+8801710000002',
			otp_code='222222',
			expires_at=timezone.now() + timedelta(minutes=10),
		)

		allowed, message = OTPVerification.can_send_otp('+8801710000002')

		self.assertFalse(allowed)
		self.assertIn('1 minute', message)

	def test_can_send_otp_blocks_after_five_requests_in_an_hour(self):
		phone = '+8801710000003'
		now = timezone.now()

		for idx in range(5):
			otp = OTPVerification.objects.create(
				phone_number=phone,
				otp_code=f'{idx:06d}',
				expires_at=now + timedelta(minutes=10),
			)
			OTPVerification.objects.filter(pk=otp.pk).update(
				created_at=now - timedelta(minutes=5, seconds=idx)
			)

		allowed, message = OTPVerification.can_send_otp(phone)

		self.assertFalse(allowed)
		self.assertIn('Too many attempts', message)

	def test_increment_attempts_reaches_max_attempts(self):
		otp = OTPVerification.objects.create(
			phone_number='+8801710000004',
			otp_code='333333',
			attempts=2,
			expires_at=timezone.now() + timedelta(minutes=10),
		)

		otp.increment_attempts()
		otp.refresh_from_db()

		self.assertEqual(otp.attempts, 3)
		self.assertTrue(otp.is_max_attempts())


class PasswordResetTokenTests(TestCase):
	def test_generate_token_invalidates_previous_active_token(self):
		user = CustomUser.objects.create_user(
			username='buyer_token',
			email='buyer_token@example.com',
			role='buyer',
			password='StrongPass123',
		)

		first = PasswordResetToken.generate_token(user)
		second = PasswordResetToken.generate_token(user)

		self.assertFalse(PasswordResetToken.objects.filter(pk=first.pk).exists())
		self.assertTrue(PasswordResetToken.objects.filter(pk=second.pk).exists())
		self.assertTrue(second.is_valid())

	def test_mark_used_makes_token_invalid(self):
		user = CustomUser.objects.create_user(
			username='buyer_token_used',
			email='buyer_used@example.com',
			role='buyer',
			password='StrongPass123',
		)
		token = PasswordResetToken.generate_token(user)

		token.mark_used()
		token.refresh_from_db()

		self.assertFalse(token.is_valid())


class DynamicRegistrationFormTests(TestCase):
	def test_farmer_pin_registration_form_is_valid_and_saves_user(self):
		form = DynamicRegistrationForm(
			data={
				'full_name': 'Farmer One',
				'phone_number': '+8801711111111',
				'role': 'farmer',
				'auth_type': 'pin',
				'pin': '1234',
				'confirm_pin': '1234',
				'district': 'Dhaka',
				'upazila': 'Sadar',
				'country': 'Bangladesh',
			}
		)

		self.assertTrue(form.is_valid(), form.errors)
		user = form.save()

		self.assertEqual(user.role, 'farmer')
		self.assertEqual(user.auth_type, 'pin')
		self.assertTrue(user.check_pin('1234'))
		self.assertTrue(user.has_usable_password())

	def test_buyer_registration_requires_documents(self):
		form = DynamicRegistrationForm(
			data={
				'full_name': 'Buyer One',
				'phone_number': '+8801722222222',
				'role': 'buyer',
				'email': 'buyer_one@example.com',
				'password': 'StrongPass123',
				'confirm_password': 'StrongPass123',
				'district': 'Dhaka',
				'upazila': 'North',
				'country': 'Bangladesh',
			}
		)

		self.assertFalse(form.is_valid())
		self.assertIn('legal_paper_photo', form.errors)
		self.assertIn('company_photo', form.errors)
