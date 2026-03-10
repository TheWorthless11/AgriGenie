"""
Celery tasks for AgriGenie
Handles all background jobs, notifications, AI retraining, and system reports.
"""

from celery import shared_task  # Use standard shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Avg, Sum
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# ==========================================
# 1. AI & WEATHER TASKS
# ==========================================
try:
    from ai_models import WeatherService, get_coordinates_from_location
except ImportError:
    WeatherService = None
    get_coordinates_from_location = None

@shared_task(bind=True, max_retries=3)
def monitor_weather_for_farmers(self):
    from farmer.models import WeatherAlert
    from users.models import Notification
    
    if not WeatherService:
        return "Weather service not available"

    try:
        farmers = User.objects.filter(role='farmer')
        for farmer in farmers:
            try:
                # Try getting location from User or FarmerProfile
                location = getattr(farmer, 'location', None)
                if not location and hasattr(farmer, 'farmer_profile'):
                    location = getattr(farmer.farmer_profile, 'farm_location', None)
                
                if not location: continue
                
                coords = get_coordinates_from_location(location)
                if not coords: continue
                
                weather_data = WeatherService.get_weather_data(coords['latitude'], coords['longitude'])
                if not weather_data: continue
                
                wind_speed = weather_data.get('wind', {}).get('speed', 0) * 3.6
                rainfall = weather_data.get('rain', {}).get('1h', 0)
                
                alerts = []
                if wind_speed > 60:
                    alerts.append({
                        'type': 'cyclone', 
                        'severity': 'critical' if wind_speed > 100 else 'high', 
                        'message': f'Strong winds ({wind_speed:.1f} km/h) detected.'
                    })
                if rainfall > 50:
                    alerts.append({
                        'type': 'flood', 
                        'severity': 'high', 
                        'message': f'Heavy rainfall ({rainfall}mm) detected.'
                    })
                
                for alert in alerts:
                    existing = WeatherAlert.objects.filter(
                        farmer=farmer, alert_type=alert['type'], is_active=True,
                        created_at__gte=timezone.now() - timedelta(hours=1)
                    ).exists()
                    
                    if not existing:
                        WeatherAlert.objects.create(
                            farmer=farmer, alert_type=alert['type'], location=location,
                            severity=alert['severity'], message=alert['message'],
                            start_time=timezone.now(), recommendation='Take precautions immediately.'
                        )
                        Notification.objects.create(
                            user=farmer, notification_type='weather', 
                            title=f'Weather Alert: {alert["type"].title()}', 
                            message=alert['message']
                        )
            except Exception as e:
                logger.error(f"Weather error for {farmer.username}: {e}")
        return "Weather monitoring completed"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=1, time_limit=3600)
def auto_retrain_price_model(self, force=False, ga_pop=8, ga_gen=5):
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    try:
        from ai_models.price_prediction.pipeline import run_pipeline
        result = run_pipeline(ga_pop=ga_pop, ga_gen=ga_gen, force=force, verbose=False)
        if result.get("status") == "skipped": return "No new data — skipped."
        m = result["metrics"]
        return f"Auto-retrain complete. RMSE={m['rmse']:.5f} MAE={m['mae']:.5f}"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)

# ==========================================
# 2. MARKETPLACE & EMAIL TASKS
# ==========================================
@shared_task
def send_notification_email(user_id, subject, message):
    from django.core.mail import send_mail
    try:
        user = User.objects.get(id=user_id)
        send_mail(subject, message, 'noreply@agrigenie.com', [user.email], fail_silently=False)
        return f'Email sent to {user.email}'
    except Exception as e:
        return f'Error: {str(e)}'

@shared_task
def send_new_listing_alerts():
    from farmer.models import Crop
    from buyer.models import WishlistItem
    from users.models import Notification
    
    four_hours_ago = timezone.now() - timedelta(hours=4)
    new_crops = Crop.objects.filter(created_at__gte=four_hours_ago, is_available=True)
    count = 0
    
    for crop in new_crops:
        interested_buyers = User.objects.filter(role='buyer', saved_crops__crop__crop_type=crop.crop_type).distinct()
        for buyer in interested_buyers:
            if not WishlistItem.objects.filter(buyer=buyer, crop=crop).exists():
                Notification.objects.create(
                    user=buyer, notification_type='order', title=f'New Listing: {crop.crop_name}',
                    message=f'New {crop.crop_type} listing available at ৳{crop.price_per_unit}'
                )
                count += 1
    return f'Sent {count} new listing alerts'

# ==========================================
# 3. MAINTENANCE & REPORTS
# ==========================================
@shared_task
def update_farmer_ratings():
    """Optimized: Updates all farmer ratings via DB Aggregation"""
    from farmer.models import FarmerRating
    from users.models import FarmerProfile
    
    # Get all average ratings in one group-by query
    ratings_data = FarmerRating.objects.values('farmer').annotate(avg_rating=Avg('rating'))
    
    updated_count = 0
    for entry in ratings_data:
        FarmerProfile.objects.filter(user_id=entry['farmer']).update(rating=entry['avg_rating'])
        updated_count += 1
        
    return f'Updated ratings for {updated_count} farmers'

@shared_task
def generate_daily_report():
    """Optimized: High-speed reporting using DB Sum/Count"""
    from admin_panel.models import SystemReport
    from farmer.models import Crop, Order
    
    today = timezone.now().date()
    delivered_orders = Order.objects.filter(status='delivered')
    
    # Calculate revenue inside the database, not in Python memory
    revenue_data = delivered_orders.aggregate(total=Sum('total_price'))
    total_revenue = revenue_data['total'] or 0
    
    report = SystemReport.objects.create(
        title=f'Daily Report - {today}',
        report_type='activity',
        total_users=User.objects.count(),
        total_farmers=User.objects.filter(role='farmer').count(),
        total_buyers=User.objects.filter(role='buyer').count(),
        total_crops_listed=Crop.objects.count(),
        total_orders=Order.objects.count(),
        total_revenue=total_revenue,
        active_listings=Crop.objects.filter(is_available=True).count(),
        content={
            'today_orders': Order.objects.filter(order_date__date=today).count(),
            'today_crops': Crop.objects.filter(created_at__date=today).count(),
            'generated_date': today.isoformat()
        }
    )
    return f'Report generated: ID {report.id}'

@shared_task
def cleanup_old_notifications():
    from users.models import Notification
    old_date = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(created_at__lt=old_date, is_read=True).delete()
    return f"Cleaned up {deleted_count} notifications"

@shared_task
def cleanup_out_of_stock_crops():
    from farmer.models import Crop
    from users.models import Notification
    
    cutoff = timezone.now() - timedelta(hours=24)
    expired_crops = Crop.objects.filter(is_available=False, out_of_stock_since__isnull=False, out_of_stock_since__lte=cutoff)
    count = 0
    for crop in expired_crops:
        Notification.objects.create(
            user=crop.farmer, notification_type='system', title=f'Listing Expired',
            message=f'Your listing for {crop.crop_name} was removed after 24h out-of-stock.'
        )
        crop.delete()
        count += 1
    return f"Cleaned up {count} crops"