from django.contrib import admin
from .models import PurchaseRequest, WishlistItem, SavedCrop, BuyerRating


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'crop', 'quantity_required', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username', 'crop__crop_name']
    readonly_fields = ['created_at', 'response_date']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'crop', 'added_date']
    search_fields = ['buyer__username', 'crop__crop_name']
    readonly_fields = ['added_date']


@admin.register(SavedCrop)
class SavedCropAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'crop', 'saved_date']
    search_fields = ['buyer__username', 'crop__crop_name']
    readonly_fields = ['saved_date']


@admin.register(BuyerRating)
class BuyerRatingAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'buyer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['farmer__username', 'buyer__username']
    readonly_fields = ['created_at']
