from django.db import models
from django.core.validators import MinValueValidator
from users.models import CustomUser
from farmer.models import Crop, Order


class PurchaseRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchase_requests')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='purchase_requests')
    quantity_required = models.FloatField(validators=[MinValueValidator(0)])
    preferred_price = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PR {self.id} - {self.crop.crop_name}"


class WishlistItem(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wishlist_items')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('buyer', 'crop')
        ordering = ['-added_date']
    
    def __str__(self):
        return f"{self.buyer.username} - {self.crop.crop_name}"


class SavedCrop(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='saved_crops')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    saved_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('buyer', 'crop')
    
    def __str__(self):
        return f"{self.buyer.username} saved {self.crop.crop_name}"


class BuyerRating(models.Model):
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='buyer_ratings_given')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_received')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('farmer', 'buyer', 'order')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating for {self.buyer.username}"
