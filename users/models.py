from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUserManager(UserManager):
    def create_user(self, username, email=None, password=None, role='buyer', **extra_fields):
        extra_fields.setdefault('role', role)
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('admin', 'Admin'),
        ('pending', 'Pending'),  # New Google users before role selection
    )
    
    AUTH_TYPE_CHOICES = (
        ('pin', 'PIN'),
        ('password', 'Password'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    # New location fields
    district = models.CharField(max_length=100, blank=True, null=True)
    upazila = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    # Farmer-specific: PIN authentication (hashed)
    auth_type = models.CharField(max_length=10, choices=AUTH_TYPE_CHOICES, default='password')
    pin_hash = models.CharField(max_length=128, blank=True, null=True)  # Hashed PIN for farmers
    
    # Buyer-specific: preferences
    preferences = models.TextField(blank=True, null=True)  # JSON or comma-separated preferences
    
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    def set_pin(self, raw_pin):
        """Hash and store the PIN securely"""
        from django.contrib.auth.hashers import make_password
        self.pin_hash = make_password(raw_pin)
    
    def check_pin(self, raw_pin):
        """Verify PIN against stored hash"""
        from django.contrib.auth.hashers import check_password
        if not self.pin_hash:
            return False
        return check_password(raw_pin, self.pin_hash)
    
    def get_full_location(self):
        """Return formatted location from district and upazila"""
        parts = []
        if self.upazila:
            parts.append(self.upazila)
        if self.district:
            parts.append(self.district)
        return ', '.join(parts) if parts else self.location
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class FarmerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=255)
    farm_size = models.FloatField(help_text="Size in acres")
    farm_location = models.CharField(max_length=255)
    soil_type = models.CharField(max_length=100)
    experience_years = models.IntegerField(default=0)
    registration_number = models.CharField(max_length=100, unique=True)
    is_approved = models.BooleanField(default=False)
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    def __str__(self):
        return self.farm_name


class BuyerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='buyer_profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_spent = models.FloatField(default=0, validators=[MinValueValidator(0)], help_text="Total amount spent on confirmed orders")
    
    def __str__(self):
        return self.company_name or self.user.username


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('order', 'Order Update'),
        ('price', 'Price Alert'),
        ('weather', 'Weather Alert'),
        ('disease', 'Disease Alert'),
        ('system', 'System Alert'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


# ============================================
# FORGOT CREDENTIAL SYSTEM MODELS
# ============================================

class OTPVerification(models.Model):
    """
    Stores OTP codes for farmer phone verification.
    - OTP expires in 5 minutes
    - Max 3 verification attempts
    - Rate limited: 1 OTP per minute, max 5 per hour
    """
    phone_number = models.CharField(max_length=20)
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, default='reset')  # 'reset', 'verify'
    attempts = models.IntegerField(default=0)  # Track failed attempts
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'otp_code']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        """Check if OTP has expired (5 minutes)"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_max_attempts(self):
        """Check if max attempts (3) reached"""
        return self.attempts >= 3
    
    def increment_attempts(self):
        """Increment failed attempts counter"""
        self.attempts += 1
        self.save()
    
    @classmethod
    def can_send_otp(cls, phone_number):
        """
        Rate limiting: Check if user can request new OTP
        - Max 1 OTP per minute
        - Max 5 OTPs per hour
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        # Check last minute
        recent_otp = cls.objects.filter(
            phone_number=phone_number,
            created_at__gte=one_minute_ago
        ).exists()
        if recent_otp:
            return False, "Please wait 1 minute before requesting another code."
        
        # Check last hour (max 5)
        hourly_count = cls.objects.filter(
            phone_number=phone_number,
            created_at__gte=one_hour_ago
        ).count()
        if hourly_count >= 5:
            return False, "Too many attempts. Please try again later."
        
        return True, None
    
    @classmethod
    def generate_otp(cls, phone_number, purpose='reset'):
        """Generate new 6-digit OTP with 5-minute expiry"""
        import random
        from django.utils import timezone
        from datetime import timedelta
        
        # Invalidate previous OTPs for this phone
        cls.objects.filter(phone_number=phone_number, is_verified=False).delete()
        
        # Generate 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Create OTP record with 10-minute expiry
        otp = cls.objects.create(
            phone_number=phone_number,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        return otp
    
    def __str__(self):
        return f"OTP for {self.phone_number} ({'expired' if self.is_expired() else 'valid'})"


class PasswordResetToken(models.Model):
    """
    Stores secure tokens for buyer email password reset.
    - Token expires in 15 minutes
    - Single use (deleted after successful reset)
    - Secure crypto-random token
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_expired(self):
        """Check if token has expired (15 minutes)"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.is_expired() and not self.is_used
    
    def mark_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save()
    
    @classmethod
    def generate_token(cls, user):
        """Generate secure reset token with 15-minute expiry"""
        import secrets
        from django.utils import timezone
        from datetime import timedelta
        
        # Invalidate previous tokens for this user
        cls.objects.filter(user=user, is_used=False).delete()
        
        # Generate secure 64-character token
        token = secrets.token_urlsafe(48)
        
        # Create token record with 15-minute expiry
        reset_token = cls.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        
        return reset_token
    
    def __str__(self):
        return f"Reset token for {self.user.email} ({'valid' if self.is_valid() else 'invalid'})"
