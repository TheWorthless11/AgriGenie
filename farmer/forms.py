from django import forms
from farmer.models import Crop, Order, Message, WeatherAlert, CropDisease


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ('crop_name', 'crop_type', 'quantity', 'unit', 'price_per_unit', 'description', 'crop_image', 'location', 'harvest_date', 'availability_date', 'quality_grade')
        widgets = {
            'crop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter crop name'}),
            'crop_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vegetable, Grain, Fruit'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'crop_image': forms.FileInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'harvest_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'availability_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quality_grade': forms.Select(attrs={'class': 'form-control'}),
        }


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
        fields = ('disease_name', 'disease_type', 'disease_image', 'treatment_recommendation')
        widgets = {
            'disease_name': forms.TextInput(attrs={'class': 'form-control'}),
            'disease_type': forms.Select(attrs={'class': 'form-control'}),
            'disease_image': forms.FileInput(attrs={'class': 'form-control'}),
            'treatment_recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
