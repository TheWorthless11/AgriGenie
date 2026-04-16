from django import forms
from admin_panel.models import MasterCrop, SystemAlert, AdminSettings
from farmer.models import IrrigationCropCatalog


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


class IrrigationCropCatalogForm(forms.ModelForm):
    """Form for admin-managed irrigation crop configuration."""

    class Meta:
        model = IrrigationCropCatalog
        fields = (
            'name',
            'water_requirement',
            'base_water_liters',
            'water_per_m2',
            'moisture_threshold',
            'retention_factor',
            'ideal_moisture',
            'irrigation_frequency_days',
            'is_active',
        )
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g., Rice',
                }
            ),
            'water_requirement': forms.Select(attrs={'class': 'form-select'}),
            'base_water_liters': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '0.1',
                }
            ),
            'water_per_m2': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'step': '0.01',
                }
            ),
            'moisture_threshold': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'max': '100',
                    'step': '1',
                }
            ),
            'retention_factor': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'max': '2',
                    'step': '0.01',
                }
            ),
            'ideal_moisture': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'max': '100',
                    'step': '1',
                }
            ),
            'irrigation_frequency_days': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'max': '30',
                    'step': '1',
                }
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = ('site_name', 'site_logo', 'default_language', 'default_timezone')
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AgriGenie'}),
            'site_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'default_language': forms.Select(attrs={'class': 'form-select'}),
            'default_timezone': forms.Select(attrs={'class': 'form-select'}),
        }


class UserManagementSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = (
            'auto_approve_new_users',
            'allow_admin_role',
            'allow_user_role',
            'allow_moderator_role',
            'max_users_limit',
            'default_new_user_role',
        )
        widgets = {
            'auto_approve_new_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_admin_role': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_user_role': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_moderator_role': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_users_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Optional'}),
            'default_new_user_role': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        role_map = {
            'admin': cleaned_data.get('allow_admin_role'),
            'user': cleaned_data.get('allow_user_role'),
            'moderator': cleaned_data.get('allow_moderator_role'),
        }

        if not any(role_map.values()):
            raise forms.ValidationError('At least one role must remain enabled.')

        default_role = cleaned_data.get('default_new_user_role')
        if default_role and not role_map.get(default_role):
            raise forms.ValidationError('Default role must be enabled in role management toggles.')

        return cleaned_data


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = (
            'email_notifications_enabled',
            'system_alert_notifications_enabled',
            'alert_threshold_percent',
            'notification_email',
        )
        widgets = {
            'email_notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'system_alert_notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alert_threshold_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100'}),
            'notification_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'alerts@example.com'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('email_notifications_enabled') and not cleaned_data.get('notification_email'):
            raise forms.ValidationError('Notification email is required when email notifications are enabled.')
        return cleaned_data


class SecuritySettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = (
            'password_min_length',
            'require_password_uppercase',
            'require_password_lowercase',
            'require_password_numbers',
            'enable_two_factor_auth',
            'session_timeout_minutes',
            'max_login_attempts',
        )
        widgets = {
            'password_min_length': forms.NumberInput(attrs={'class': 'form-control', 'min': '6', 'max': '64'}),
            'require_password_uppercase': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_password_lowercase': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_password_numbers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_two_factor_auth': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'session_timeout_minutes': forms.Select(attrs={'class': 'form-select'}),
            'max_login_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
        }


class AiFeatureSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = (
            'enable_ai_recommendations',
            'ai_model_version',
            'ai_api_key',
            'enable_disease_detection',
        )
        widgets = {
            'enable_ai_recommendations': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_model_version': forms.Select(attrs={'class': 'form-select'}),
            'ai_api_key': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter API key'}, render_value=True),
            'enable_disease_detection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = ('maintenance_mode',)
        widgets = {
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
