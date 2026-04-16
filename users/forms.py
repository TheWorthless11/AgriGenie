from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from users.models import (
    CustomUser,
    FarmerProfile,
    BuyerProfile,
    FarmerSettings,
    FarmerPaymentMethod,
)
import re


# Bangladesh Districts and Upazilas
BANGLADESH_DISTRICTS = [
    ('', 'Select District'),
    ('Dhaka', 'Dhaka'),
    ('Chittagong', 'Chittagong'),
    ('Rajshahi', 'Rajshahi'),
    ('Khulna', 'Khulna'),
    ('Sylhet', 'Sylhet'),
    ('Barishal', 'Barishal'),
    ('Rangpur', 'Rangpur'),
    ('Mymensingh', 'Mymensingh'),
    ('Comilla', 'Comilla'),
    ('Gazipur', 'Gazipur'),
    ('Narayanganj', 'Narayanganj'),
    ('Bogra', 'Bogra'),
    ('Jessore', 'Jessore'),
    ('Cox\'s Bazar', 'Cox\'s Bazar'),
    ('Dinajpur', 'Dinajpur'),
    ('Tangail', 'Tangail'),
    ('Faridpur', 'Faridpur'),
    ('Brahmanbaria', 'Brahmanbaria'),
    ('Narsingdi', 'Narsingdi'),
]

# Sample Upazilas - In production, this would be dynamic based on district
SAMPLE_UPAZILAS = [
    ('', 'Select Upazila'),
    ('Sadar', 'Sadar'),
    ('North', 'North'),
    ('South', 'South'),
    ('East', 'East'),
    ('West', 'West'),
]


class CustomUserCreationForm(UserCreationForm):
    """Legacy form - kept for backwards compatibility"""
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.RadioSelect()
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class DynamicRegistrationForm(forms.ModelForm):
    """
    Dynamic registration form that handles both Farmer and Buyer registration.
    Fields change based on the selected role.
    """
    
    # Common fields
    full_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +8801XXXXXXXXX'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('farmer', 'Farmer'), ('buyer', 'Buyer')],
        initial='farmer',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Location fields - moved to onboarding wizard
    district = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())
    upazila = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())
    country = forms.CharField(max_length=100, initial='Bangladesh', required=False, widget=forms.HiddenInput())
    profile_picture = forms.ImageField(required=False, widget=forms.HiddenInput())
    
    # Farmer-specific fields
    auth_type = forms.ChoiceField(
        choices=[('pin', 'PIN'), ('password', 'Password')],
        initial='pin',
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    pin = forms.CharField(
        min_length=4,
        max_length=6,
        required=False,
        validators=[RegexValidator(r'^\d{4,6}$', 'PIN must be 4-6 digits only.')],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 4-6 digit PIN',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
    
    confirm_pin = forms.CharField(
        min_length=4,
        max_length=6,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your PIN',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
    
    # Password fields (for buyer or farmer with password auth)
    password = forms.CharField(
        min_length=8,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 characters'
        })
    )
    
    confirm_password = forms.CharField(
        min_length=8,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Buyer-specific fields
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    # Document upload fields for buyer approval (REQUIRED for buyers)
    legal_paper_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    company_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    # Preferences moved to onboarding wizard
    preferences = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = CustomUser
        fields = ['phone_number']
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Remove any spaces or dashes
        phone = re.sub(r'[\s\-]', '', phone)
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        role = self.cleaned_data.get('role')
        
        if role == 'buyer':
            if not email:
                raise forms.ValidationError("Email is required for buyers.")
        
        # Check for duplicate email if provided
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        
        return email
    
    def clean_pin(self):
        pin = self.cleaned_data.get('pin')
        role = self.cleaned_data.get('role')
        auth_type = self.cleaned_data.get('auth_type')
        
        if role == 'farmer' and auth_type == 'pin':
            if not pin:
                raise forms.ValidationError("PIN is required for farmers using PIN authentication.")
            if not pin.isdigit():
                raise forms.ValidationError("PIN must contain only digits.")
            if len(pin) < 4 or len(pin) > 6:
                raise forms.ValidationError("PIN must be 4-6 digits.")
        return pin
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        role = self.cleaned_data.get('role')
        auth_type = self.cleaned_data.get('auth_type')
        
        needs_password = (role == 'buyer') or (role == 'farmer' and auth_type == 'password')
        
        if needs_password:
            
            if not password:
                raise forms.ValidationError("Password is required.")
            if len(password) < 8:
                raise forms.ValidationError("Password must be at least 8 characters.")
            if not re.search(r'[A-Z]', password):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[a-z]', password):
                raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r'\d', password):
                raise forms.ValidationError("Password must contain at least one number.")
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        auth_type = cleaned_data.get('auth_type')
        
        # Validate PIN confirmation for farmers
        if role == 'farmer' and auth_type == 'pin':
            pin = cleaned_data.get('pin')
            confirm_pin = cleaned_data.get('confirm_pin')
            if pin and confirm_pin and pin != confirm_pin:
                self.add_error('confirm_pin', "PINs do not match.")
        
        # Validate password confirmation
        needs_password = (role == 'buyer') or (role == 'farmer' and auth_type == 'password')
        if needs_password:
            password = cleaned_data.get('password')
            confirm_password = cleaned_data.get('confirm_password')
            if password and confirm_password and password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")

        # Validate buyer documents are required
        if role == 'buyer':
            if not cleaned_data.get('legal_paper_photo'):
                self.add_error('legal_paper_photo', 'Legal papers photo is required for buyer approval.')
            if not cleaned_data.get('company_photo'):
                self.add_error('company_photo', 'Company photo is required for buyer approval.')
        
        return cleaned_data
    
    def save(self, commit=True):
        # Create username from phone number
        phone = self.cleaned_data.get('phone_number')
        username = phone.replace('+', '').replace(' ', '')[-10:]  # Use last 10 digits
        
        # Check if username exists, append number if needed
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        role = self.cleaned_data.get('role', 'farmer')
        # For farmers, check auth_type; for buyers, always use password
        if role == 'farmer':
            auth_type = self.cleaned_data.get('auth_type') or 'pin'  # Default to pin for farmers
        else:
            auth_type = 'password'  # Buyers always use password
        
        user = CustomUser(
            username=username,
            first_name=self.cleaned_data.get('full_name', ''),
            phone_number=self.cleaned_data.get('phone_number'),
            email=self.cleaned_data.get('email', ''),
            role=role,
            district=self.cleaned_data.get('district'),
            upazila=self.cleaned_data.get('upazila'),
            country=self.cleaned_data.get('country', 'Bangladesh'),
            preferences=self.cleaned_data.get('preferences', ''),
            auth_type=auth_type,
        )
        
        # Handle profile picture
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data.get('profile_picture')
        
        # Set password or PIN based on auth type
        if role == 'farmer' and auth_type == 'pin':
            pin = self.cleaned_data.get('pin')
            if pin:
                user.set_pin(pin)
            # Also set a random password for Django auth system (PIN used for actual login)
            import secrets
            user.set_password(secrets.token_urlsafe(32))
        else:
            password = self.cleaned_data.get('password')
            if password:
                user.set_password(password)
        
        if commit:
            user.save()
        
        return user


class CustomUserChangeForm(UserChangeForm):
    password = None
    
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'location', 'profile_picture', 'bio')


class AdminProfileUpdateForm(forms.ModelForm):
    """Focused profile edit form for admin accounts."""

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and CustomUser.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if phone and CustomUser.objects.exclude(pk=self.instance.pk).filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already in use by another account.')
        return phone


class FarmerAccountSettingsForm(forms.ModelForm):
    """Account section for farmer settings page."""

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and CustomUser.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email

    def clean_phone_number(self):
        phone = (self.cleaned_data.get('phone_number') or '').strip()
        if phone and CustomUser.objects.exclude(pk=self.instance.pk).filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already in use by another account.')
        return phone


class FarmerPreferenceSettingsForm(forms.ModelForm):
    """Farm preference section for farmer settings page."""

    DEFAULT_CROP_CHOICES = [
        ('', 'Select default crop type'),
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('maize', 'Maize'),
        ('potato', 'Potato'),
        ('tomato', 'Tomato'),
        ('onion', 'Onion'),
    ]

    default_crop_type = forms.ChoiceField(
        choices=DEFAULT_CROP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = FarmerSettings
        fields = ('quantity_unit', 'farm_size_unit', 'default_crop_type', 'language')
        widgets = {
            'quantity_unit': forms.Select(attrs={'class': 'form-select'}),
            'farm_size_unit': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_crop = (getattr(self.instance, 'default_crop_type', '') or '').strip().lower()
        known_values = [choice[0] for choice in self.DEFAULT_CROP_CHOICES if choice[0]]
        if current_crop and current_crop not in known_values:
            self.fields['default_crop_type'].choices = self.DEFAULT_CROP_CHOICES + [
                (current_crop, current_crop.replace('_', ' ').title())
            ]


class FarmerNotificationSettingsForm(forms.ModelForm):
    """Notification toggle section for farmer settings page."""

    class Meta:
        model = FarmerSettings
        fields = ('email_notifications', 'sms_alerts', 'order_updates', 'ai_alerts')
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FarmerAISettingsForm(forms.ModelForm):
    """AI setting section for farmer settings page."""

    class Meta:
        model = FarmerSettings
        fields = ('disease_detection_enabled', 'auto_recommendations', 'risk_sensitivity')
        widgets = {
            'disease_detection_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_recommendations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'risk_sensitivity': forms.Select(attrs={'class': 'form-select'}),
        }


class FarmerPaymentMethodForm(forms.ModelForm):
    """Payment method add/edit form."""

    class Meta:
        model = FarmerPaymentMethod
        fields = ('method_type', 'account_name', 'account_number', 'bank_name')
        widgets = {
            'method_type': forms.Select(attrs={'class': 'form-select', 'id': 'paymentMethodType'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account holder name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account/mobile number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank name (for bank account)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        method_type = cleaned_data.get('method_type')
        bank_name = (cleaned_data.get('bank_name') or '').strip()

        if method_type == 'bank' and not bank_name:
            self.add_error('bank_name', 'Bank name is required for bank account method.')

        return cleaned_data


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = FarmerProfile
        fields = ('farm_name', 'farm_size', 'farm_location', 'soil_type', 'experience_years', 'registration_number')
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'form-control'}),
            'farm_size': forms.NumberInput(attrs={'class': 'form-control'}),
            'farm_location': forms.TextInput(attrs={'class': 'form-control'}),
            'soil_type': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FarmerProfileBasicForm(forms.ModelForm):
    """Profile edit form for farmer basic details shown in profile edit UI."""

    class Meta:
        model = FarmerProfile
        fields = ('farm_name', 'farm_size', 'farm_location')
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'form-control'}),
            'farm_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'farm_location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ('company_name', 'business_type', 'registration_number')
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
