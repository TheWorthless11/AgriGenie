from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_customuser_two_factor_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='FarmerPaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('method_type', models.CharField(choices=[('bkash', 'bKash'), ('nagad', 'Nagad'), ('bank', 'Bank Account')], max_length=20)),
                ('account_name', models.CharField(max_length=120)),
                ('account_number', models.CharField(max_length=60)),
                ('bank_name', models.CharField(blank=True, max_length=120, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='farmer_payment_methods', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FarmerSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_unit', models.CharField(choices=[('kg', 'Kilogram (kg)'), ('ton', 'Ton'), ('quintal', 'Quintal'), ('piece', 'Piece')], default='kg', max_length=20)),
                ('farm_size_unit', models.CharField(choices=[('acre', 'Acre'), ('hectare', 'Hectare')], default='acre', max_length=20)),
                ('default_crop_type', models.CharField(blank=True, max_length=100, null=True)),
                ('language', models.CharField(choices=[('en', 'English'), ('bn', 'Bangla')], default='en', max_length=10)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_alerts', models.BooleanField(default=False)),
                ('order_updates', models.BooleanField(default=True)),
                ('ai_alerts', models.BooleanField(default=True)),
                ('disease_detection_enabled', models.BooleanField(default=True)),
                ('auto_recommendations', models.BooleanField(default=True)),
                ('risk_sensitivity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='farmer_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Farmer Settings',
                'verbose_name_plural': 'Farmer Settings',
            },
        ),
    ]
