from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser


class MasterCrop(models.Model):
    """
    Master Crop Template - Admin creates these to define what crops are allowed on the platform.
    Farmers select from these when posting their crops for sale.
    """
    CROP_CATEGORIES = (
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('grains', 'Grains'),
        ('pulses', 'Pulses'),
        ('spices', 'Spices'),
        ('cash_crops', 'Cash Crops'),
        ('other', 'Other'),
    )
    
    CROP_TYPES = (
        ('organic', 'Organic'),
        ('conventional', 'Conventional'),
        ('hybrid', 'Hybrid'),
    )
    
    crop_name = models.CharField(max_length=100, unique=True, help_text="Name of the crop (e.g., Tomato, Rice)")
    crop_type = models.CharField(max_length=50, choices=CROP_TYPES, default='conventional')
    category = models.CharField(max_length=50, choices=CROP_CATEGORIES)
    description = models.TextField(blank=True, null=True, help_text="General description of this crop")
    generic_image = models.ImageField(upload_to='master_crops/', blank=True, null=True, help_text="Generic crop image")
    is_active = models.BooleanField(default=True, help_text="Is this crop available for farmers to list?")
    allow_detection = models.BooleanField(default=True, help_text="Allow farmers to run AI disease detection on this crop type")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_master_crops')
    
    class Meta:
        ordering = ['crop_name']
        verbose_name = 'Master Crop Template'
        verbose_name_plural = 'Master Crop Templates'
    
    def __str__(self):
        return f"{self.crop_name} ({self.get_category_display()})"


class UserApproval(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='approval_request')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    documents = models.FileField(upload_to='approvals/', null=True, blank=True)
    legal_paper_photo = models.ImageField(upload_to='approvals/legal/', null=True, blank=True)
    company_photo = models.ImageField(upload_to='approvals/company/', null=True, blank=True)
    reason_for_rejection = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"


class SystemAlert(models.Model):
    ALERT_TYPES = (
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('feature', 'Feature Update'),
        ('warning', 'Warning'),
        ('info', 'Information'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    is_active = models.BooleanField(default=True)
    target_users = models.ManyToManyField(
        CustomUser,
        related_name='system_alerts',
        blank=True
    )
    all_users = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alerts'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class SystemReport(models.Model):
    title = models.CharField(max_length=255)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('user_stats', 'User Statistics'),
            ('crop_stats', 'Crop Statistics'),
            ('order_stats', 'Order Statistics'),
            ('revenue', 'Revenue Report'),
            ('activity', 'Activity Report'),
        ]
    )
    total_users = models.IntegerField(default=0)
    total_farmers = models.IntegerField(default=0)
    total_buyers = models.IntegerField(default=0)
    total_crops_listed = models.IntegerField(default=0)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.FloatField(default=0)
    active_listings = models.IntegerField(default=0)
    content = models.JSONField(default=dict)  # Store detailed report data as JSON
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return self.title


class AIDiseaseMonitor(models.Model):
    total_detections = models.IntegerField(default=0)
    accurate_detections = models.IntegerField(default=0)
    accuracy_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_updated = models.DateTimeField(auto_now=True)
    model_version = models.CharField(max_length=50, default='1.0')
    
    def __str__(self):
        return f"Disease Detection - {self.accuracy_percentage}%"


class AIPricePredictor(models.Model):
    total_predictions = models.IntegerField(default=0)
    accurate_predictions = models.IntegerField(default=0)
    accuracy_percentage = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    last_updated = models.DateTimeField(auto_now=True)
    model_version = models.CharField(max_length=50, default='1.0')
    average_error_percentage = models.FloatField(default=0)
    
    def __str__(self):
        return f"Price Prediction - {self.accuracy_percentage}%"


class UserReport(models.Model):
    """Reports/feedback submitted by users about the website"""
    REPORT_TYPES = (
        ('bug', 'Bug Report'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submitted_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.subject} ({self.get_status_display()})"


class ActivityLog(models.Model):
    ACTION_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create_crop', 'Create Crop'),
        ('update_crop', 'Update Crop'),
        ('delete_crop', 'Delete Crop'),
        ('place_order', 'Place Order'),
        ('cancel_order', 'Cancel Order'),
        ('upload_image', 'Upload Image'),
        ('send_message', 'Send Message'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"

class FarmerListing(models.Model):
    """
    Farmer's actual stock for sale, linked to a MasterCrop template.
    """
    QUALITY_GRADES = (
        ('grade_a', 'Grade A (Excellent)'),
        ('grade_b', 'Grade B (Good)'),
        ('grade_c', 'Grade C (Standard)'),
    )

    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='listings')
    crop_template = models.ForeignKey(MasterCrop, on_delete=models.CASCADE, related_name='farmer_listings')
    
    quantity = models.FloatField(validators=[MinValueValidator(0.1)])
    unit = models.CharField(max_length=20, default='kg') # e.g., kg, ton, piece
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    location = models.CharField(max_length=255)
    harvest_date = models.DateField()
    availability_date = models.DateField()
    quality_grade = models.CharField(max_length=20, choices=QUALITY_GRADES, default='grade_b')
    
    is_available = models.BooleanField(default=True)
    specific_description = models.TextField(blank=True, null=True, help_text="Details about THIS specific batch")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.crop_template.crop_name} ({self.quantity}{self.unit})"