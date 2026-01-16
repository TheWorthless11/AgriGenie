from django.contrib import admin
from .models import CropListing, Review, Search, CategoryFilter, PriceHistory


@admin.register(CropListing)
class CropListingAdmin(admin.ModelAdmin):
    list_display = ['crop', 'is_featured', 'views_count', 'inquiry_count', 'order_count']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['crop__crop_name', 'crop__farmer__username']
    readonly_fields = ['views_count', 'inquiry_count', 'order_count']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['crop', 'reviewer', 'rating', 'verified_purchase', 'created_at']
    list_filter = ['rating', 'verified_purchase', 'created_at']
    search_fields = ['crop__crop_name', 'reviewer__username']
    readonly_fields = ['created_at']


@admin.register(Search)
class SearchAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__username']
    readonly_fields = ['created_at']


@admin.register(CategoryFilter)
class CategoryFilterAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['crop', 'price', 'recorded_date']
    list_filter = ['recorded_date']
    search_fields = ['crop__crop_name']
    readonly_fields = ['recorded_date']
    date_hierarchy = 'recorded_date'
