from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, FarmerProfile, BuyerProfile, Notification


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'location', 'profile_picture', 'bio', 'is_verified')}),
    )
    list_display = ['username', 'email', 'role', 'is_verified', 'is_active']
    list_filter = BaseUserAdmin.list_filter + ('role', 'is_verified')
    search_fields = ['username', 'email', 'phone_number', 'location']


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'user', 'farm_location', 'is_approved', 'rating']
    list_filter = ['is_approved', 'soil_type']
    search_fields = ['farm_name', 'user__username', 'farm_location']
    readonly_fields = ['rating']


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'business_type', 'is_approved', 'rating']
    list_filter = ['is_approved', 'business_type']
    search_fields = ['company_name', 'user__username']
    readonly_fields = ['rating']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at']
