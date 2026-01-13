from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from users.models import CustomUser, FarmerProfile, BuyerProfile


class CustomUserCreationForm(UserCreationForm):
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


class CustomUserChangeForm(UserChangeForm):
    password = None
    
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'location', 'profile_picture', 'bio')


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


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ('company_name', 'business_type', 'registration_number')
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
