"""
Celery tasks for AgriGenie
Handles background jobs like weather monitoring and price predictions
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from farmer.models import WeatherAlert, Crop, CropPrice
from users.models import Notification
from ai_models import WeatherService, get_coordinates_from_location
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def monitor_weather_for_farmers(self):
    """
    Background task to monitor weather and generate alerts for farmers
    Runs periodically (every hour or as configured)
    """
    try:
        farmers = User.objects.filter(role='farmer')
        
        for farmer in farmers:
            try:
                # Get farmer's location
                location = getattr(farmer, 'location', None) or \
                          getattr(farmer.farmer_profile, 'farm_location', None) \
                          if hasattr(farmer, 'farmer_profile') else None
                
                if not location:
                    continue
                
                # Get coordinates
                coords = get_coordinates_from_location(location)
                if not coords:
                    continue
                
                # Get weather data
                weather_data = WeatherService.get_weather_data(
                    coords['latitude'],
                    coords['longitude']
                )
                
                if not weather_data:
                    continue
                
                # Check for alerts
                wind_speed = weather_data.get('wind', {}).get('speed', 0) * 3.6  # Convert to km/h
                rainfall = weather_data.get('rain', {}).get('1h', 0)
                
                # Generate appropriate alerts
                alerts = []
                
                # Check for cyclone/high wind
                if wind_speed > 60:
                    alerts.append({
                        'type': 'cyclone',
                        'severity': 'critical' if wind_speed > 100 else 'high',
                        'message': f'Strong winds ({wind_speed:.1f} km/h) detected in your area'
                    })
                
                # Check for flood risk
                if rainfall > 50:
                    alerts.append({
                        'type': 'flood',
                        'severity': 'high',
                        'message': f'Heavy rainfall ({rainfall}mm) detected. Risk of flooding.'
                    })
                
                # Create weather alert records for farmer
                for alert in alerts:
                    # Check if similar alert already exists
                    existing = WeatherAlert.objects.filter(
                        farmer=farmer,
                        alert_type=alert['type'],
                        is_active=True,
                        created_at__gte=datetime.now() - timedelta(hours=1)
                    ).first()
                    
                    if not existing:
                        weather_alert = WeatherAlert.objects.create(
                            farmer=farmer,
                            alert_type=alert['type'],
                            location=location,
                            severity=alert['severity'],
                            message=alert['message'],
                            start_time=datetime.now(),
                            recommendation='Monitor situation and take necessary precautions'
                        )
                        
                        # Create notification
                        Notification.objects.create(
                            user=farmer,
                            notification_type='weather',
                            title=f'Weather Alert: {alert["type"].title()}',
                            message=alert['message']
                        )
                
            except Exception as e:
                logger.error(f"Error monitoring weather for farmer {farmer.username}: {e}")
                continue
        
        logger.info("Weather monitoring task completed successfully")
        return "Weather monitoring completed"
    
    except Exception as exc:
        logger.error(f"Error in weather monitoring task: {exc}")
        # Retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def update_price_predictions(self):
    """
    Background task to update price predictions for all crops
    Runs daily
    """
    try:
        crops = Crop.objects.filter(is_available=True)
        
        for crop in crops:
            try:
                # Only keep last 30 days of predictions
                old_predictions = CropPrice.objects.filter(
                    crop=crop,
                    prediction_date__lt=datetime.now().date() - timedelta(days=30)
                )
                old_predictions.delete()
                
            except Exception as e:
                logger.error(f"Error updating predictions for crop {crop.id}: {e}")
                continue
        
        logger.info(f"Updated price predictions for {crops.count()} crops")
        return f"Price predictions updated for {crops.count()} crops"
    
    except Exception as exc:
        logger.error(f"Error in price prediction update task: {exc}")
        return f"Error: {str(exc)}"


@shared_task
def send_price_alerts():
    """
    Background task to send price change notifications
    Alerts farmers when crop prices change significantly
    """
    try:
        # Get crops with price predictions
        crop_prices = CropPrice.objects.filter(
            prediction_date=datetime.now().date()
        ).select_related('crop', 'crop__farmer')
        
        for price_record in crop_prices:
            crop = price_record.crop
            
            # Check if price changed significantly (>10%)
            previous_price = crop.price_per_unit
            predicted_price = price_record.predicted_price
            
            change_percent = abs((predicted_price - previous_price) / previous_price * 100)
            
            if change_percent > 10:
                Notification.objects.create(
                    user=crop.farmer,
                    notification_type='price',
                    title=f'Price Change Alert: {crop.crop_name}',
                    message=f'Predicted price will change by {change_percent:.1f}%. Current: ₹{previous_price}, Predicted: ₹{predicted_price:.2f}'
                )
                logger.info(f"Price alert sent for {crop.crop_name}")
        
        return f"Price alerts sent"
    
    except Exception as exc:
        logger.error(f"Error in price alert task: {exc}")
        return f"Error: {str(exc)}"


@shared_task
def cleanup_old_notifications():
    """
    Background task to clean up old notifications
    Removes notifications older than 30 days
    """
    try:
        from users.models import Notification
        
        old_date = datetime.now() - timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(
            created_at__lt=old_date,
            is_read=True
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return f"Cleaned up {deleted_count} notifications"
    
    except Exception as exc:
        logger.error(f"Error in cleanup task: {exc}")
        return f"Error: {str(exc)}"
