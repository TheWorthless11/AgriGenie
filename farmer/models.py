from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from django.utils import timezone


class Crop(models.Model):
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='crops')
    crop_name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=100)
    quantity = models.FloatField(validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=20, default='kg')  # kg, tons, etc.
    price_per_unit = models.FloatField(validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, null=True)
    crop_image = models.ImageField(upload_to='crops/')
    location = models.CharField(max_length=255)
    harvest_date = models.DateField()
    availability_date = models.DateField()
    quality_grade = models.CharField(
        max_length=20,
        choices=[('A', 'Grade A'), ('B', 'Grade B'), ('C', 'Grade C')],
        default='B'
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.crop_name} - {self.farmer.username}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='orders')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='buyer_orders')
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='farmer_orders')
    quantity = models.FloatField(validators=[MinValueValidator(0)])
    total_price = models.FloatField(validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    special_requirements = models.TextField(blank=True, null=True)
    is_confirmed_by_buyer = models.BooleanField(default=False)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order {self.id} - {self.crop.crop_name}"


class CropDisease(models.Model):
    DISEASE_TYPES = (
        ('fungal', 'Fungal Disease'),
        ('bacterial', 'Bacterial Disease'),
        ('viral', 'Viral Disease'),
        ('pest', 'Pest Damage'),
    )
    
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='diseases')
    disease_name = models.CharField(max_length=100)
    disease_type = models.CharField(max_length=20, choices=DISEASE_TYPES)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    disease_image = models.ImageField(upload_to='disease_uploads/')
    treatment_recommendation = models.TextField()
    detected_date = models.DateTimeField(auto_now_add=True)
    ai_model_used = models.CharField(max_length=100, default='ResNet50')
    
    def __str__(self):
        return f"{self.disease_name} on {self.crop.crop_name}"


class CropPrice(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='price_history')
    predicted_price = models.FloatField()
    actual_price = models.FloatField(null=True, blank=True)
    prediction_date = models.DateField(auto_now_add=True)
    forecast_days = models.IntegerField(default=30)  # Price forecast for next N days
    confidence_level = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    class Meta:
        ordering = ['-prediction_date']
    
    def __str__(self):
        return f"{self.crop.crop_name} - {self.prediction_date}"


class WeatherAlert(models.Model):
    ALERT_TYPES = (
        ('flood', 'Flood'),
        ('drought', 'Drought'),
        ('cyclone', 'Cyclone'),
        ('heavy_rain', 'Heavy Rain'),
        ('frost', 'Frost'),
        ('heat_wave', 'Heat Wave'),
    )
    
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='weather_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    location = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')]
    )
    message = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    recommendation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.location}"


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    attachment = models.FileField(upload_to='messages/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"


class FarmerRating(models.Model):
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_ratings')
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('farmer', 'buyer', 'order')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating} stars - {self.farmer.username}"
