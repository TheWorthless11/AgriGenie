from django.contrib import admin
from .models import (
    Crop,
    Order,
    CropDisease,
    WeatherAlert,
    Message,
    FarmerRating,
    IrrigationCropCatalog,
    IrrigationCrop,
    IrrigationRecord,
    IrrigationSchedule,
)


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'farmer', 'quantity', 'price_per_unit', 'is_available', 'created_at']
    list_filter = ['is_available', 'quality_grade', 'harvest_date']
    search_fields = ['crop_name', 'farmer__username', 'location']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'crop', 'buyer', 'farmer', 'quantity', 'status', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['crop__crop_name', 'buyer__username', 'farmer__username']
    readonly_fields = ['order_date', 'confirmation_date']
    date_hierarchy = 'order_date'


@admin.register(CropDisease)
class CropDiseaseAdmin(admin.ModelAdmin):
    list_display = ['disease_name', 'crop', 'disease_type', 'confidence_score', 'detected_date']
    list_filter = ['disease_type', 'detected_date']
    search_fields = ['disease_name', 'crop__crop_name']
    readonly_fields = ['detected_date']


@admin.register(WeatherAlert)
class WeatherAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'location', 'severity', 'farmer', 'is_active', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_active']
    search_fields = ['location', 'farmer__username']
    readonly_fields = ['created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'subject']
    readonly_fields = ['created_at']


@admin.register(FarmerRating)
class FarmerRatingAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'buyer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['farmer__username', 'buyer__username']
    readonly_fields = ['created_at']


@admin.register(IrrigationCrop)
class IrrigationCropAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'water_requirement', 'base_water_liters', 'ideal_moisture', 'irrigation_frequency_days', 'updated_at']
    list_filter = ['water_requirement', 'updated_at']
    search_fields = ['name', 'farmer__username']


@admin.register(IrrigationCropCatalog)
class IrrigationCropCatalogAdmin(admin.ModelAdmin):
    list_display = ['name', 'water_requirement', 'base_water_liters', 'ideal_moisture', 'irrigation_frequency_days', 'is_active', 'updated_at']
    list_filter = ['water_requirement', 'is_active', 'updated_at']
    search_fields = ['name']


@admin.register(IrrigationRecord)
class IrrigationRecordAdmin(admin.ModelAdmin):
    list_display = ['crop', 'date', 'water_amount', 'method', 'created_at']
    list_filter = ['method', 'date']
    search_fields = ['crop__name', 'crop__farmer__username']
    readonly_fields = ['created_at']


@admin.register(IrrigationSchedule)
class IrrigationScheduleAdmin(admin.ModelAdmin):
    list_display = ['crop', 'next_irrigation_date', 'frequency_days', 'updated_at']
    list_filter = ['next_irrigation_date', 'frequency_days']
    search_fields = ['crop__name', 'crop__farmer__username']
