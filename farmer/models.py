from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from django.utils import timezone


class Crop(models.Model):
    """
    Farmer's Crop Listing - Actual crops posted for sale by farmers.
    Must reference a MasterCrop template created by admin.
    """
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='crops')
    master_crop = models.ForeignKey('admin_panel.MasterCrop', on_delete=models.PROTECT, related_name='listings', null=True, blank=True, help_text="Select crop type from admin's master list")
    
    # Farmer-specific details for their listing
    quantity = models.FloatField(validators=[MinValueValidator(0)], help_text="Available quantity")
    unit = models.CharField(max_length=20, default='kg', choices=[('kg', 'Kilograms'), ('tons', 'Tons'), ('quintals', 'Quintals'), ('pieces', 'Pieces')])
    price_per_unit = models.FloatField(validators=[MinValueValidator(0)], help_text="Price per unit")
    location = models.CharField(max_length=255, help_text="Farm/pickup location")
    harvest_date = models.DateField(help_text="When was this crop harvested?")
    availability_date = models.DateField(help_text="When is it available for sale/pickup?")
    quality_grade = models.CharField(
        max_length=20,
        choices=[('A', 'Grade A - Premium'), ('B', 'Grade B - Standard'), ('C', 'Grade C - Basic')],
        default='B',
        help_text="Quality grade of your crop"
    )
    area_size = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.01)],
        help_text='Field size used for irrigation planning',
    )
    area_unit = models.CharField(
        max_length=10,
        choices=[('m2', 'm²'), ('acre', 'Acre'), ('hectare', 'Hectare')],
        default='m2',
        help_text='Unit of the field size (m², acre, hectare)',
    )
    
    # Optional farmer details
    description = models.TextField(blank=True, null=True, help_text="Additional details about your specific crop listing")
    crop_image = models.ImageField(upload_to='crops/', blank=True, null=True, help_text="Photo of YOUR actual crop (optional)")
    
    # System fields
    is_available = models.BooleanField(default=True)
    out_of_stock_since = models.DateTimeField(null=True, blank=True, help_text="When crop went out of stock (auto-deletes after 24h)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Crop Listing'
        verbose_name_plural = 'Crop Listings'
    
    def __str__(self):
        name = self.master_crop.crop_name if self.master_crop else 'Unknown Crop'
        return f"{name} - {self.farmer.username} ({self.quantity}{self.unit})"
    
    @property
    def crop_name(self):
        """For backward compatibility with existing code"""
        return self.master_crop.crop_name if self.master_crop else 'Unknown Crop'
    
    @property
    def crop_type(self):
        """For backward compatibility with existing code"""
        return self.master_crop.crop_type if self.master_crop else 'Unknown'

    @property
    def area_size_m2(self):
        """Normalize listing area into square meters."""
        factor = AREA_TO_M2_FACTOR.get(str(self.area_unit or 'm2').lower(), 1.0)
        return round(float(self.area_size or 0) * factor, 2)
    
    def deduct_quantity(self, amount):
        """Deduct quantity when order is accepted. Mark out-of-stock if zero."""
        self.quantity = max(0, self.quantity - amount)
        if self.quantity <= 0:
            self.quantity = 0
            self.is_available = False
            self.out_of_stock_since = timezone.now()
        self.save()
    
    def restore_quantity(self, amount):
        """Restore quantity when order is cancelled/rejected."""
        self.quantity += amount
        if self.quantity > 0:
            self.is_available = True
            self.out_of_stock_since = None
        self.save()


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
        ('healthy', 'Healthy'),
    )

    # Either `crop` (a farmer's listing) OR `master_crop` (admin template) should be provided.
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, related_name='diseases', null=True, blank=True)
    master_crop = models.ForeignKey('admin_panel.MasterCrop', on_delete=models.SET_NULL, related_name='master_diseases', null=True, blank=True)
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disease_detections', null=True, blank=True)

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
        crop_name = self.crop.crop_name if self.crop else (self.master_crop.crop_name if self.master_crop else 'Unknown')
        return f"{self.disease_name} on {crop_name}"


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


class CropPriceData(models.Model):
    """
    Stores actual observed crop-price records.
    Only real historical/monthly data — never predicted values.
    Unique on (Year, Month, Market, Commodity, Variety).
    """
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    market = models.CharField(max_length=60)
    commodity = models.CharField(max_length=60)
    variety = models.CharField(max_length=80)

    price_per_kg = models.FloatField()
    avg_temp_c = models.FloatField()
    max_temp_c = models.FloatField()
    min_temp_c = models.FloatField()
    rainfall_mm = models.FloatField()
    cumulative_rainfall_mm = models.FloatField()
    flood = models.IntegerField(default=0)
    drought = models.IntegerField(default=0)
    yield_per_hectare = models.FloatField()
    production_tonnes = models.FloatField()
    area_hectares = models.FloatField()
    import_tonnes = models.FloatField()
    export_tonnes = models.FloatField()
    fertilizer_cost = models.FloatField()
    seed_cost = models.FloatField()
    labor_cost = models.FloatField()
    fuel_cost = models.FloatField()
    inflation = models.FloatField()
    cpi = models.FloatField()
    lag1_price = models.FloatField()
    lag2_price = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('year', 'month', 'market', 'commodity', 'variety')
        ordering = ['year', 'month', 'market', 'commodity', 'variety']
        verbose_name = 'Crop Price Data'
        verbose_name_plural = 'Crop Price Data'

    def __str__(self):
        return f"{self.commodity}/{self.variety} - {self.market} ({self.month}/{self.year})"


IRRIGATION_WATER_REQUIREMENT_CHOICES = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
)

AREA_UNIT_CHOICES = (
    ('m2', 'm²'),
    ('acre', 'Acre'),
    ('hectare', 'Hectare'),
)

AREA_TO_M2_FACTOR = {
    'm2': 1.0,
    'acre': 4046.86,
    'hectare': 10000.0,
}


class IrrigationCropCatalog(models.Model):
    """Admin-controlled crop catalog for irrigation settings."""

    name = models.CharField(max_length=100, unique=True)
    water_requirement = models.CharField(
        max_length=10,
        choices=IRRIGATION_WATER_REQUIREMENT_CHOICES,
        default='medium',
    )
    base_water_liters = models.FloatField(validators=[MinValueValidator(0)], default=9.0)
    water_per_m2 = models.FloatField(validators=[MinValueValidator(0)], default=2.0)
    moisture_threshold = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=45,
    )
    retention_factor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        default=0.5,
    )
    ideal_moisture = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    irrigation_frequency_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        default=3,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Irrigation Crop Catalog'
        verbose_name_plural = 'Irrigation Crop Catalog'

    def __str__(self):
        return f"{self.name.title()} ({self.water_requirement})"


class IrrigationCrop(models.Model):
    """Farmer-specific crop profile used by irrigation planning."""

    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='irrigation_crops')
    name = models.CharField(max_length=100)
    area_size = models.FloatField(default=1.0, validators=[MinValueValidator(0.01)])
    area_unit = models.CharField(max_length=10, choices=AREA_UNIT_CHOICES, default='m2')
    water_requirement = models.CharField(max_length=10, choices=IRRIGATION_WATER_REQUIREMENT_CHOICES, default='medium')
    base_water_liters = models.FloatField(validators=[MinValueValidator(0)], default=9.0)
    water_per_m2 = models.FloatField(validators=[MinValueValidator(0)], default=2.0)
    moisture_threshold = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=45,
    )
    retention_factor = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        default=0.5,
    )
    ideal_moisture = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    irrigation_frequency_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        default=3,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('farmer', 'name')

    def __str__(self):
        return f"{self.name.title()} ({self.water_requirement}, {self.base_water_liters}L)"

    @property
    def area_size_m2(self):
        """Normalize crop area into square meters."""
        factor = AREA_TO_M2_FACTOR.get(str(self.area_unit or 'm2').lower(), 1.0)
        return round(float(self.area_size or 0) * factor, 2)


class IrrigationRecord(models.Model):
    """Logged irrigation events for water usage tracking."""

    METHOD_CHOICES = (
        ('manual', 'Manual'),
        ('pump', 'Pump'),
        ('drip', 'Drip'),
        ('automatic', 'Automatic (Legacy)'),
    )

    crop = models.ForeignKey(IrrigationCrop, on_delete=models.CASCADE, related_name='irrigation_records', null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='irrigation_records', null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    water_amount = models.FloatField(validators=[MinValueValidator(0)])
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        crop_name = self.crop.name if self.crop else 'Unknown Crop'
        return f"{crop_name} - {self.water_amount}L on {self.date}"


class IrrigationSchedule(models.Model):
    """Persisted next-irrigation schedule derived from crop and weather."""

    crop = models.OneToOneField(IrrigationCrop, on_delete=models.CASCADE, related_name='irrigation_schedule')
    next_irrigation_date = models.DateField()
    frequency_days = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    recommendation = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_irrigation_date']

    def __str__(self):
        return f"{self.crop.name} -> {self.next_irrigation_date} (every {self.frequency_days} days)"
