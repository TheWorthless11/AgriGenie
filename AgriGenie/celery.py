"""
Celery configuration and tasks for AgriGenie
"""

from celery import Celery, shared_task
from celery.schedules import crontab
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import os

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriGenie.settings')

app = Celery('AgriGenie')

# Load configuration from Django settings with a namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure periodic tasks
app.conf.beat_schedule = {
    'monitor-weather-every-hour': {
        'task': 'AgriGenie.tasks.monitor_weather_for_farmers',
        'schedule': crontab(minute=0),  # Every hour
    },
    'update-price-predictions-daily': {
        'task': 'AgriGenie.tasks.update_price_predictions',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
    },
    'send-price-alerts-daily': {
        'task': 'AgriGenie.tasks.send_price_alerts',
        'schedule': crontab(hour=6, minute=0),  # Every day at 6 AM
    },
    'cleanup-old-notifications-weekly': {
        'task': 'AgriGenie.tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Every Sunday at 2 AM
    },
}

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


@shared_task
def send_notification_email(user_id, subject, message):
    """Send notification email to user"""
    from users.models import CustomUser
    try:
        user = CustomUser.objects.get(id=user_id)
        send_mail(
            subject,
            message,
            'noreply@agrigenie.com',
            [user.email],
            fail_silently=False,
        )
        return f'Email sent to {user.email}'
    except CustomUser.DoesNotExist:
        return f'User {user_id} not found'
    except Exception as e:
        return f'Error sending email: {str(e)}'


@shared_task
def check_weather_alerts():
    """
    Periodically check weather conditions and create alerts
    Runs every 6 hours
    """
    from farmer.models import WeatherAlert
    from users.models import CustomUser, Notification
    from ai_models.weather_service import WeatherService, generate_weather_alert
    
    farmers = CustomUser.objects.filter(role='farmer')
    
    for farmer in farmers:
        try:
            # Get farmer's location
            location = farmer.location or farmer.farmer_profile.farm_location
            if not location:
                continue
            
            # Get weather data
            weather_summary = WeatherService.get_weather_summary(
                farmer.location or 'Default',
                farmer.location or 'Default'
            )
            
            if not weather_summary:
                continue
            
            # Create alerts for detected disasters
            for alert in weather_summary.get('alerts', []):
                # Check if alert already exists
                existing = WeatherAlert.objects.filter(
                    farmer=farmer,
                    alert_type=alert['type'],
                    is_active=True,
                    created_at__gte=timezone.now() - timedelta(hours=2)
                ).exists()
                
                if not existing:
                    # Create new alert
                    weather_alert = WeatherAlert.objects.create(
                        farmer=farmer,
                        alert_type=alert['type'],
                        location=location,
                        severity=alert['severity'],
                        message=alert['message'],
                        start_time=timezone.now(),
                        recommendation=alert['recommendation'],
                        is_active=True
                    )
                    
                    # Create notification
                    Notification.objects.create(
                        user=farmer,
                        notification_type='weather',
                        title=f'Weather Alert: {alert["type"].title()}',
                        message=alert['message']
                    )
        except Exception as e:
            print(f"Error checking weather alerts for farmer {farmer.id}: {str(e)}")
            continue
    
    return 'Weather alerts checked'


@shared_task
def generate_price_predictions():
    """
    Generate price predictions for all available crops
    Runs daily
    """
    from farmer.models import Crop, CropPrice
    from ai_models.price_prediction import predict_crop_prices
    
    crops = Crop.objects.filter(is_available=True)
    
    for crop in crops:
        try:
            current_price = crop.price_per_unit
            
            # Generate predictions
            result = predict_crop_prices(current_price, days_ahead=30)
            
            # Store first prediction
            if result['predictions']:
                first_pred = result['predictions'][0]
                CropPrice.objects.create(
                    crop=crop,
                    predicted_price=first_pred['price'],
                    prediction_date=timezone.now().date(),
                    confidence_level=75.0,
                    forecast_days=30
                )
        except Exception as e:
            print(f"Error generating price predictions for crop {crop.id}: {str(e)}")
            continue
    
    return f'Price predictions generated for {crops.count()} crops'


@shared_task
def send_price_alerts():
    """
    Send price change alerts to farmers
    Runs every 12 hours
    """
    from farmer.models import Crop, CropPrice
    from users.models import Notification
    from django.db.models import F, Q
    
    # Check crops with significant price changes
    yesterday = timezone.now() - timedelta(days=1)
    
    price_changes = CropPrice.objects.filter(
        prediction_date__gte=yesterday.date()
    ).select_related('crop__farmer')
    
    for price_record in price_changes:
        try:
            crop = price_record.crop
            
            # Calculate percentage change
            if crop.price_per_unit > 0:
                change_percent = (
                    (price_record.predicted_price - crop.price_per_unit) / 
                    crop.price_per_unit * 100
                )
                
                if abs(change_percent) > 5:  # Alert if change > 5%
                    direction = "increased" if change_percent > 0 else "decreased"
                    
                    Notification.objects.create(
                        user=crop.farmer,
                        notification_type='price',
                        title=f'Price Alert: {crop.crop_name}',
                        message=f'Price has {direction} by {abs(change_percent):.1f}% to ৳{price_record.predicted_price:.2f}'
                    )
        except Exception as e:
            print(f"Error sending price alert: {str(e)}")
            continue
    
    return f'Price alerts sent for {price_changes.count()} crops'


@shared_task
def send_new_listing_alerts():
    """
    Send alerts to buyers about new listings matching their interests
    Runs every 4 hours
    """
    from farmer.models import Crop
    from buyer.models import SavedCrop, WishlistItem
    from users.models import CustomUser, Notification
    
    # Get crops created in last 4 hours
    four_hours_ago = timezone.now() - timedelta(hours=4)
    new_crops = Crop.objects.filter(
        created_at__gte=four_hours_ago,
        is_available=True
    )
    
    alert_count = 0
    
    for crop in new_crops:
        try:
            # Find buyers interested in this crop type
            interested_buyers = CustomUser.objects.filter(
                role='buyer',
                saved_crops__crop__crop_type=crop.crop_type
            ).distinct()
            
            for buyer in interested_buyers:
                # Check if not already in wishlist
                if not WishlistItem.objects.filter(buyer=buyer, crop=crop).exists():
                    Notification.objects.create(
                        user=buyer,
                        notification_type='order',
                        title=f'New Listing: {crop.crop_name}',
                        message=f'New {crop.crop_type} listing available at ৳{crop.price_per_unit} per {crop.unit}'
                    )
                    alert_count += 1
        except Exception as e:
            print(f"Error sending new listing alert for crop {crop.id}: {str(e)}")
            continue
    
    return f'Sent {alert_count} new listing alerts'


@shared_task
def cleanup_old_notifications():
    """
    Delete read notifications older than 30 days
    Runs daily
    """
    from users.models import Notification
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=thirty_days_ago
    ).delete()
    
    return f'Cleaned up {deleted_count} old notifications'


@shared_task
def update_farmer_ratings():
    """
    Update farmer average ratings based on recent reviews
    Runs daily
    """
    from farmer.models import FarmerRating
    from users.models import FarmerProfile, CustomUser
    from django.db.models import Avg
    
    farmers = CustomUser.objects.filter(role='farmer')
    
    for farmer in farmers:
        try:
            avg_rating = FarmerRating.objects.filter(
                farmer=farmer
            ).aggregate(avg=Avg('rating'))['avg']
            
            if avg_rating:
                profile = FarmerProfile.objects.filter(user=farmer).first()
                if profile:
                    profile.rating = avg_rating
                    profile.save()
        except Exception as e:
            print(f"Error updating farmer rating: {str(e)}")
            continue
    
    return f'Updated ratings for {farmers.count()} farmers'


@shared_task
def generate_daily_report():
    """
    Generate daily system report
    Runs daily at 11:59 PM
    """
    from admin_panel.models import SystemReport
    from farmer.models import Crop, Order
    from users.models import CustomUser
    from django.utils import timezone
    
    today = timezone.now().date()
    
    total_users = CustomUser.objects.count()
    total_farmers = CustomUser.objects.filter(role='farmer').count()
    total_buyers = CustomUser.objects.filter(role='buyer').count()
    total_crops = Crop.objects.count()
    total_orders = Order.objects.count()
    total_revenue = sum([o.total_price for o in Order.objects.filter(status='delivered')])
    
    today_orders = Order.objects.filter(order_date__date=today).count()
    today_crops = Crop.objects.filter(created_at__date=today).count()
    
    report = SystemReport.objects.create(
        title=f'Daily Report - {today}',
        report_type='activity',
        total_users=total_users,
        total_farmers=total_farmers,
        total_buyers=total_buyers,
        total_crops_listed=total_crops,
        total_orders=total_orders,
        total_revenue=total_revenue,
        active_listings=Crop.objects.filter(is_available=True).count(),
        content={
            'today_orders': today_orders,
            'today_crops': today_crops,
            'generated_date': today.isoformat()
        }
    )
    
    return f'Daily report generated with ID {report.id}'


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
    return 'Debug task executed'
