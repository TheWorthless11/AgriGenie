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
    """
    Monitor weather conditions for all farmers and send alerts when dangerous weather is detected.
    Checks for: floods, storms, heavy rain, extreme temperatures, high winds, drought risk
    """
    from farmer.models import WeatherAlert
    from users.models import Notification
    
    if not WeatherService:
        return "Weather service not available"

    try:
        farmers = User.objects.filter(role='farmer')
        alert_count = 0
        
        for farmer in farmers:
            try:
                # Get farmer's location
                location = getattr(farmer, 'location', None)
                if not location and hasattr(farmer, 'farmer_profile'):
                    location = getattr(farmer.farmer_profile, 'farm_location', None)
                
                if not location:
                    continue
                
                # Get coordinates from location
                coords = get_coordinates_from_location(location)
                if not coords:
                    continue
                
                # Fetch current weather data
                weather_data = WeatherService.get_weather_data(
                    coords['latitude'], 
                    coords['longitude']
                )
                if not weather_data:
                    continue
                
                # Extract weather parameters
                main_data = weather_data.get('main', {})
                wind_data = weather_data.get('wind', {})
                rain_data = weather_data.get('rain', {})
                clouds_data = weather_data.get('clouds', {})
                weather_list = weather_data.get('weather', [{}])
                weather_condition = weather_list[0].get('main', '').lower()
                weather_description = weather_list[0].get('description', '').lower()
                
                temperature = main_data.get('temp', 0)
                humidity = main_data.get('humidity', 0)
                pressure = main_data.get('pressure', 0)
                wind_speed = wind_data.get('speed', 0) * 3.6  # Convert m/s to km/h
                rainfall = rain_data.get('1h', 0)
                cloud_cover = clouds_data.get('all', 0)
                
                # Detect adverse weather conditions
                alerts_to_create = _detect_adverse_weather_conditions(
                    farmer=farmer,
                    location=location,
                    temperature=temperature,
                    humidity=humidity,
                    pressure=pressure,
                    wind_speed=wind_speed,
                    rainfall=rainfall,
                    weather_condition=weather_condition,
                    weather_description=weather_description,
                    cloud_cover=cloud_cover
                )
                
                # Create alerts and notifications
                for alert_config in alerts_to_create:
                    # Check if alert already exists (avoid duplicates)
                    existing_alert = WeatherAlert.objects.filter(
                        farmer=farmer,
                        alert_type=alert_config['type'],
                        is_active=True,
                        created_at__gte=timezone.now() - timedelta(hours=2)
                    ).exists()
                    
                    if not existing_alert:
                        # Create WeatherAlert
                        WeatherAlert.objects.create(
                            farmer=farmer,
                            alert_type=alert_config['type'],
                            location=location,
                            severity=alert_config['severity'],
                            message=alert_config['message'],
                            start_time=timezone.now(),
                            recommendation=alert_config['recommendation']
                        )
                        
                        # Send notification to farmer
                        Notification.objects.create(
                            user=farmer,
                            notification_type='weather',
                            title=f"⚠️ Weather Alert: {alert_config['title']}",
                            message=alert_config['notification_message']
                        )
                        
                        alert_count += 1
                        logger.info(
                            f"Weather alert created for {farmer.username}: "
                            f"{alert_config['type']} ({alert_config['severity']}) - {location}"
                        )
                
            except Exception as e:
                logger.error(f"Error processing weather for farmer {farmer.username}: {e}")
                continue
        
        return f"Weather monitoring completed. {alert_count} alerts created."
    
    except Exception as exc:
        logger.error(f"Weather monitoring task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


def _detect_adverse_weather_conditions(farmer, location, temperature, humidity, pressure, 
                                      wind_speed, rainfall, weather_condition, 
                                      weather_description, cloud_cover):
    """
    Detect adverse weather conditions and return list of alerts to create.
    Checks for conditions that are harmful for farming and crop growth.
    """
    alerts = []
    
    # 1. FLOOD RISK - Heavy rainfall or rain with high humidity
    if rainfall > 50:
        alerts.append({
            'type': 'flood',
            'severity': 'critical' if rainfall > 100 else 'high',
            'title': '🌊 Flood Alert',
            'message': f'Heavy rainfall ({rainfall}mm/hr) detected.',
            'notification_message': (
                f'Severe flooding risk detected in {location} with {rainfall}mm of rainfall! '
                'Ensure proper drainage, move equipment to higher ground, and monitor water levels closely. '
                '⚠️ This is a severe weather event.'
            ),
            'recommendation': (
                f'IMMEDIATE ACTION REQUIRED:\n'
                f'• Ensure proper field drainage\n'
                f'• Move farm equipment to higher ground\n'
                f'• Monitor water levels closely\n'
                f'• Check for crop damage after rainfall\n'
                f'• Document any losses for insurance'
            )
        })
    elif rainfall > 30 and humidity > 85:
        alerts.append({
            'type': 'flood',
            'severity': 'high',
            'title': '🌧️ Heavy Rain Warning',
            'message': f'Heavy rainfall ({rainfall}mm/hr) with high humidity.',
            'notification_message': (
                f'Heavy rain warning for {location}! With {rainfall}mm rainfall and high humidity, '
                'there is risk of flooding and water stagnation affecting your crops.'
            ),
            'recommendation': (
                'ACTION NEEDED:\n'
                '• Ensure field drainage is functioning\n'
                '• Avoid planting or watering temporarily\n'
                '• Check drainage canals and remove blockages\n'
                '• Monitor weather updates'
            )
        })
    
    # 2. STORM/THUNDERSTORM WARNING
    if 'thunderstorm' in weather_description or 'thunder' in weather_condition:
        alerts.append({
            'type': 'cyclone',
            'severity': 'critical',
            'title': '⛈️ Thunderstorm Warning',
            'message': f'Thunderstorm conditions detected.',
            'notification_message': (
                f'Thunderstorm warning for {location}! Risk of lightning, heavy winds, and hail. '
                'Move livestock to shelter and secure all loose materials immediately.'
            ),
            'recommendation': (
                'IMMEDIATE SAFETY ACTION:\n'
                '• Move livestock to shelter\n'
                '• Secure loose farm structures and equipment\n'
                '• Turn off electrical equipment and irrigation systems\n'
                '• Stay indoors during lightning\n'
                '• Check for crop and structural damage after storm'
            )
        })
    
    # 3. CYCLONE/SEVERE WIND WARNING
    if wind_speed > 80:
        alerts.append({
            'type': 'cyclone',
            'severity': 'critical',
            'title': '🌪️ Severe Wind Alert',
            'message': f'Extreme wind speed ({wind_speed:.1f} km/h) detected.',
            'notification_message': (
                f'CRITICAL: Severe wind warning ({wind_speed:.1f} km/h) for {location}! '
                'Risk of crop damage, structural collapse. Seek shelter and secure property immediately.'
            ),
            'recommendation': (
                'CRITICAL ACTION:\n'
                '• Secure/harvest crops immediately if possible\n'
                '• Move equipment indoors\n'
                '• Reinforce temporary structures\n'
                '• Bring livestock to sheltered areas\n'
                '• Stay indoors away from windows'
            )
        })
    elif wind_speed > 60:
        alerts.append({
            'type': 'cyclone',
            'severity': 'high',
            'title': '💨 High Wind Alert',
            'message': f'Strong winds ({wind_speed:.1f} km/h) detected.',
            'notification_message': (
                f'High wind warning ({wind_speed:.1f} km/h) for {location}. '
                'Strong winds pose risk to standing crops and loose structures.'
            ),
            'recommendation': (
                'PRECAUTIONS NEEDED:\n'
                f'• Wind speed: {wind_speed:.1f} km/h (potentially damaging)\n'
                '• Secure loose materials and equipment\n'
                '• Consider harvesting vulnerable crops\n'
                '• Check crops for lodging/bending\n'
                '• Avoid spraying operations'
            )
        })
    elif wind_speed > 40:
        alerts.append({
            'type': 'cyclone',
            'severity': 'medium',
            'title': '🌬️ Strong Wind Warning',
            'message': f'Strong winds ({wind_speed:.1f} km/h) expected.',
            'notification_message': (
                f'Strong wind conditions ({wind_speed:.1f} km/h) in {location}. '
                'Monitor crops for damage and reschedule any spraying operations.'
            ),
            'recommendation': (
                'RECOMMENDATIONS:\n'
                f'• Wind speed: {wind_speed:.1f} km/h\n'
                '• Postpone spraying and foliar applications\n'
                '• Monitor for crop lodging (bending/falling)\n'
                '• Avoid unnecessary field operations'
            )
        })
    
    # 4. FROST WARNING
    if temperature < 0:
        alerts.append({
            'type': 'frost',
            'severity': 'critical' if temperature < -5 else 'high',
            'title': '❄️ Frost Alert',
            'message': f'Freezing conditions detected ({temperature}°C).',
            'notification_message': (
                f'Frost alert for {location}! Temperature has dropped to {temperature}°C. '
                'Sensitive crops and seedlings are at risk of frost damage.'
            ),
            'recommendation': (
                'FROST PROTECTION:\n'
                f'• Current temperature: {temperature}°C\n'
                '• Cover tender plants with cloth or straw\n'
                '• Initiate frost protection measures immediately\n'
                '• Avoid watering during frost hours\n'
                '• Monitor for crop damage after frost'
            )
        })
    
    # 5. HEAT WAVE WARNING
    elif temperature > 40:
        alerts.append({
            'type': 'heat_wave',
            'severity': 'high',
            'title': '🔥 Heat Wave Alert',
            'message': f'Extreme heat detected ({temperature}°C).',
            'notification_message': (
                f'Heat wave warning for {location}! Temperature reached {temperature}°C. '
                'Your crops need immediate irrigation and may experience heat stress.'
            ),
            'recommendation': (
                'HEAT STRESS MANAGEMENT:\n'
                f'• Current temperature: {temperature}°C (extremely hot)\n'
                '• Increase irrigation frequency\n'
                '• Apply mulch to retain soil moisture\n'
                '• Avoid fertilizing during heat stress\n'
                '• Use shade cloth for sensitive crops if available'
            )
        })
    elif temperature > 35:
        alerts.append({
            'type': 'heat_wave',
            'severity': 'medium',
            'title': '☀️ High Temperature Alert',
            'message': f'High temperature detected ({temperature}°C).',
            'notification_message': (
                f'High temperature warning for {location}! Conditions at {temperature}°C '
                'may cause heat stress. Monitor moisture levels closely.'
            ),
            'recommendation': (
                'HEAT MANAGEMENT:\n'
                f'• Current temperature: {temperature}°C (hot)\n'
                '• Ensure adequate soil moisture through irrigation\n'
                '• Monitor crops for wilting or heat stress\n'
                '• Avoid spraying during peak heat (10 AM - 4 PM)'
            )
        })
    
    # 6. DROUGHT RISK - Low humidity and no rain expected
    if humidity < 30:
        alerts.append({
            'type': 'drought',
            'severity': 'high' if humidity < 20 else 'medium',
            'title': '🏜️ Drought Risk Alert',
            'message': f'Very low humidity ({humidity}%) detected - drought risk.',
            'notification_message': (
                f'Drought conditions developing in {location}! Humidity is very low at {humidity}%. '
                'Increase irrigation to prevent crop stress and water shortages.'
            ),
            'recommendation': (
                'DROUGHT MANAGEMENT:\n'
                f'• Current humidity: {humidity}% (critically low)\n'
                '• Increase irrigation frequency\n'
                '• Mulch fields to reduce evaporation\n'
                '• Check soil moisture regularly\n'
                '• Prioritize water for critical growth stages'
            )
        })
    
    # 7. POOR VISIBILITY - Fog, mist, haze (affects pesticide application)
    if 'fog' in weather_description or 'mist' in weather_description or 'haze' in weather_description:
        alerts.append({
            'type': 'other',
            'severity': 'low',
            'title': '🌫️ Poor Visibility Notice',
            'message': f'Poor visibility conditions ({weather_description}).',
            'notification_message': (
                f'Poor visibility warning for {location}. '
                'Spraying operations not recommended due to low visibility affecting coverage.'
            ),
            'recommendation': (
                'FARMING OPERATIONS:\n'
                '• Postpone spraying until visibility improves\n'
                '• Be cautious during field operations\n'
                '• Use lights on farm equipment\n'
                '• Monitor driving conditions'
            )
        })
    
    # 8. PRESSURE DROP WARNING - May indicate approaching storm
    if pressure < 1000:
        alerts.append({
            'type': 'other',
            'severity': 'medium',
            'title': '📉 Atmospheric Pressure Drop',
            'message': f'Low atmospheric pressure ({pressure} hPa) - storm approaching.',
            'notification_message': (
                f'Weather alert for {location}! Falling atmospheric pressure ({pressure} hPa) '
                'indicates a weather system is approaching. Prepare for potential storms.'
            ),
            'recommendation': (
                'STORM PREPARATION:\n'
                f'• Current pressure: {pressure} hPa (low)\n'
                '• Secure all equipment and structures\n'
                '• Monitor weather forecasts closely\n'
                '• Prepare emergency measures\n'
                '• Postpone field work if storm expected'
            )
        })
    
    return alerts

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