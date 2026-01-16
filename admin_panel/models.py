from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser


class UserApproval(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='approval_request')
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    documents = models.FileField(upload_to='approvals/', null=True, blank=True)
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
