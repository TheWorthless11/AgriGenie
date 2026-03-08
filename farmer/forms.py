from django import forms
from farmer.models import Crop, Order, Message, WeatherAlert, CropDisease
from admin_panel.models import MasterCrop


class CropForm(forms.ModelForm):
    """Form for Farmer to post crops for sale - must select from admin's master crop list"""
    class Meta:
        model = Crop
        fields = ('master_crop', 'quantity', 'unit', 'price_per_unit', 'location', 'harvest_date', 'availability_date', 'quality_grade', 'description', 'crop_image')
        widgets = {
            'master_crop': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Enter quantity available'
            }),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Price per unit'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Farm/pickup location'
            }),
            'harvest_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'availability_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'quality_grade': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about your crop (optional)'
            }),
            'crop_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'master_crop': 'Select Crop Type',
            'price_per_unit': 'Price Per Unit',
            'crop_image': 'Upload Photo of Your Crop (Optional)',
        }
        help_texts = {
            'master_crop': 'Select the type of crop you want to sell',
            'crop_image': 'Upload a photo of YOUR actual crop. If not provided, generic crop image will be used.',
            'quality_grade': 'Quality grade of your crop',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active master crops - required field
        self.fields['master_crop'].queryset = MasterCrop.objects.filter(is_active=True)
        self.fields['master_crop'].required = True
        self.fields['master_crop'].empty_label = '-- Select a crop from the list --'


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('quantity', 'delivery_date', 'special_requirements')
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'message', 'attachment')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class WeatherAlertForm(forms.ModelForm):
    class Meta:
        model = WeatherAlert
        fields = ('alert_type', 'location', 'severity', 'message', 'start_time', 'end_time', 'recommendation')
        widgets = {
            'alert_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CropDiseaseForm(forms.ModelForm):
    class Meta:
        model = CropDisease
        fields = ('disease_name', 'disease_type', 'disease_image', 'treatment_recommendation', 'master_crop')
        widgets = {
            'disease_name': forms.TextInput(attrs={'class': 'form-control'}),
            'disease_type': forms.Select(attrs={'class': 'form-control'}),
            'disease_image': forms.FileInput(attrs={'class': 'form-control'}),
            'treatment_recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'master_crop': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show master crops that are active and allowed for detection
        self.fields['master_crop'].queryset = MasterCrop.objects.filter(is_active=True, allow_detection=True)
