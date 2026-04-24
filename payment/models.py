from django.db import models
from django.core.validators import MinValueValidator
from users.models import CustomUser
from farmer.models import Order
import uuid


class Payment(models.Model):
    """Track all payments for orders"""
    
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Cash on Delivery'),
        ('sslcommerz', 'Online Payment (SSLCommerz)'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('initiating', 'Initiating Payment'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    # Unique Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    
    # Payment Details
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cod'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Amount Details
    total_amount = models.FloatField(validators=[MinValueValidator(0)])
    paid_amount = models.FloatField(default=0.0, validators=[MinValueValidator(0)])
    
    # For COD: Track upfront payment and remaining balance
    upfront_amount = models.FloatField(default=0.0, validators=[MinValueValidator(0)])  # 20% for COD
    remaining_amount = models.FloatField(default=0.0, validators=[MinValueValidator(0)])  # 80% for COD
    
    # SSLCommerz Transaction Details
    transaction_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    ssl_session_id = models.CharField(max_length=255, null=True, blank=True)
    ssl_validation_id = models.CharField(max_length=255, null=True, blank=True)
    ssl_error_message = models.TextField(null=True, blank=True)
    
    # Transaction Tracking
    initiated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Refund Details
    refunded_at = models.DateTimeField(null=True, blank=True)
    refund_status = models.CharField(max_length=50, null=True, blank=True)
    refund_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment {self.id} - Order {self.order.id} - {self.status}"
    
    def get_payment_gateway_message(self):
        """Get readable message about payment gateway"""
        if self.payment_method == 'cod':
            return f"Cash on Delivery - Pay ৳{self.upfront_amount:.2f} upfront, ৳{self.remaining_amount:.2f} at delivery"
        else:
            return f"Online Payment via SSLCommerz - Pay ৳{self.total_amount:.2f}"


class PaymentGatewayConfig(models.Model):
    """Configuration for SSLCommerz payment gateway"""
    
    store_id = models.CharField(max_length=255)
    store_password = models.CharField(max_length=255)
    session_api_url = models.URLField(default='https://sandbox.sslcommerz.com/gwprocess/v4/api.php')
    validation_api_url = models.URLField(default='https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php')
    
    is_active = models.BooleanField(default=True)
    is_sandbox = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Gateway Config'
        verbose_name_plural = 'Payment Gateway Configs'
    
    def __str__(self):
        return f"SSLCommerz Config - {'Sandbox' if self.is_sandbox else 'Live'}"


class PaymentLog(models.Model):
    """Detailed logs for payment transactions"""
    
    LOG_TYPE_CHOICES = (
        ('request', 'Request to Gateway'),
        ('response', 'Response from Gateway'),
        ('validation', 'Validation Request'),
        ('error', 'Error'),
        ('info', 'Information'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    message = models.TextField()
    request_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Log'
        verbose_name_plural = 'Payment Logs'
    
    def __str__(self):
        return f"Log - {self.payment.id} - {self.log_type}"
