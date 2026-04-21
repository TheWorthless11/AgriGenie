# Generated migration for Payment models

from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('farmer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentGatewayConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('store_id', models.CharField(max_length=255)),
                ('store_password', models.CharField(max_length=255)),
                ('session_api_url', models.URLField(default='https://sandbox.sslcommerz.com/gwprocess/v4/api.php')),
                ('validation_api_url', models.URLField(default='https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php')),
                ('is_active', models.BooleanField(default=True)),
                ('is_sandbox', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Payment Gateway Config',
                'verbose_name_plural': 'Payment Gateway Configs',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('payment_method', models.CharField(choices=[('cod', 'Cash on Delivery'), ('sslcommerz', 'Online Payment (SSLCommerz)')], default='cod', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('initiating', 'Initiating Payment'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('total_amount', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('paid_amount', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0)])),
                ('upfront_amount', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0)])),
                ('remaining_amount', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0)])),
                ('transaction_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('ssl_session_id', models.CharField(blank=True, max_length=255, null=True)),
                ('ssl_validation_id', models.CharField(blank=True, max_length=255, null=True)),
                ('ssl_error_message', models.TextField(blank=True, null=True)),
                ('initiated_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('refund_status', models.CharField(blank=True, max_length=50, null=True)),
                ('refund_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='farmer.order')),
            ],
            options={
                'verbose_name': 'Payment',
                'verbose_name_plural': 'Payments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_type', models.CharField(choices=[('request', 'Request to Gateway'), ('response', 'Response from Gateway'), ('validation', 'Validation Request'), ('error', 'Error'), ('info', 'Information')], max_length=20)),
                ('message', models.TextField()),
                ('request_data', models.JSONField(blank=True, null=True)),
                ('response_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='payment.payment')),
            ],
            options={
                'verbose_name': 'Payment Log',
                'verbose_name_plural': 'Payment Logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
