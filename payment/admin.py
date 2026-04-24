from django.contrib import admin
from .models import Payment, PaymentGatewayConfig, PaymentLog


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'payment_method', 'status', 'total_amount', 'paid_amount', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order__id', 'transaction_id', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'initiated_at', 'completed_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'total_amount', 'paid_amount')
        }),
        ('COD Details', {
            'fields': ('upfront_amount', 'remaining_amount'),
            'classes': ('collapse',)
        }),
        ('SSLCommerz Details', {
            'fields': ('transaction_id', 'ssl_session_id', 'ssl_validation_id', 'ssl_error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('initiated_at', 'completed_at', 'created_at', 'updated_at')
        }),
        ('Refund Information', {
            'fields': ('refunded_at', 'refund_status', 'refund_id'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ['store_id', 'is_active', 'is_sandbox', 'updated_at']
    list_filter = ['is_active', 'is_sandbox']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['payment', 'log_type', 'created_at']
    list_filter = ['log_type', 'created_at']
    search_fields = ['payment__id', 'message']
    readonly_fields = ['created_at']
