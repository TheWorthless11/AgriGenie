from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from farmer.models import Crop


class CropListing(models.Model):
    crop = models.OneToOneField(Crop, on_delete=models.CASCADE, related_name='listing')
    is_featured = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    inquiry_count = models.IntegerField(default=0)
    order_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.crop.crop_name} - Listing"


class Review(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=255)
    review_text = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('crop', 'reviewer')
    
    def __str__(self):
        return f"Review by {self.reviewer.username} on {self.crop.crop_name}"


class Search(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    query = models.CharField(max_length=255)
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Search: {self.query}"


class CategoryFilter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name


class PriceHistory(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='price_history_logs')
    price = models.FloatField()
    recorded_date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_date']
    
    def __str__(self):
        return f"{self.crop.crop_name} - {self.price}"
