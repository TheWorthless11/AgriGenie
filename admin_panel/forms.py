from django import forms
from admin_panel.models import MasterCrop, SystemAlert


class MasterCropForm(forms.ModelForm):
    """Form for Admin to create Master Crop Templates - No image, farmers upload their own"""
    class Meta:
        model = MasterCrop
        fields = ('crop_name', 'crop_type', 'category', 'description', 'is_active')
        widgets = {
            'crop_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Tomato, Rice, Wheat'
            }),
            'crop_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'General description of this crop type'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'crop_name': 'Unique name for this crop type',
            'is_active': 'Uncheck to temporarily disable this crop from farmer listings',
        }


class SystemAlertForm(forms.ModelForm):
    """Form for creating system-wide alerts"""
    class Meta:
        model = SystemAlert
        fields = ('title', 'message', 'alert_type', 'all_users', 'target_users', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'alert_type': forms.Select(attrs={'class': 'form-control'}),
            'all_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_users': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
