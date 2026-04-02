from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from farmer.models import (
    Crop,
    Order,
    CropDisease,
    WeatherAlert,
    Message,
    FarmerRating,
    IrrigationCrop,
    IrrigationRecord,
    IrrigationSchedule,
)
from farmer.forms import CropForm, OrderForm, MessageForm, WeatherAlertForm, CropDiseaseForm
from farmer.services.irrigation import (
    ensure_default_irrigation_crops,
    ensure_schedule_defaults,
    generate_irrigation_plan,
    upsert_irrigation_schedule,
    build_usage_summary,
    default_frequency_days_for_crop,
)
from users.models import Notification, CustomUser, FarmerProfile
from admin_panel.models import MasterCrop
from marketplace.models import CropListing
from buyer.models import PurchaseRequest
from ai_models import analyze_disease_image
from collections import Counter
from datetime import datetime, timedelta
import logging
import requests
import numpy as np
from sklearn.linear_model import LinearRegression
import json


logger = logging.getLogger(__name__)

OPENWEATHER_FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
WEATHER_CACHE_TTL_SECONDS = 30 * 60
WEATHER_FORECAST_DAYS = 5
ALERT_PRIORITY_ORDER = ('rain', 'humidity', 'temperature', 'wind', 'other')

COUNTRY_NAME_OVERRIDES = {
    'BD': 'Bangladesh',
    'IN': 'India',
    'PK': 'Pakistan',
    'NP': 'Nepal',
    'LK': 'Sri Lanka',
    'US': 'United States',
    'GB': 'United Kingdom',
    'AE': 'United Arab Emirates',
}


def _kelvin_to_celsius(temp_kelvin):
    """Convert Kelvin temperature to Celsius with 2 decimal precision."""
    if temp_kelvin is None:
        return None
    return round(float(temp_kelvin) - 273.15, 2)


def _parse_coordinate(value, name, min_value, max_value):
    """Parse and validate latitude/longitude query parameters."""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'Invalid {name}. Must be a number.')

    if parsed < min_value or parsed > max_value:
        raise ValueError(f'Invalid {name}. Must be between {min_value} and {max_value}.')

    return parsed


def _weather_cache_key(lat, lon):
    """Build a stable cache key for coordinate-based weather lookups."""
    return f'api_weather_v5_{lat:.4f}_{lon:.4f}'


def _cache_get_safe(key):
    """Read from cache without failing the API if cache backend is down."""
    try:
        return cache.get(key)
    except Exception as exc:
        logger.warning('Weather cache get failed for key=%s: %s', key, exc)
        return None


def _cache_set_safe(key, value, timeout_seconds):
    """Write to cache without failing the API if cache backend is down."""
    try:
        cache.set(key, value, timeout_seconds)
    except Exception as exc:
        logger.warning('Weather cache set failed for key=%s: %s', key, exc)


def _fetch_openweather_forecast(lat, lon):
    """Fetch raw 5-day/3-hour forecast data from OpenWeatherMap."""
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', None)
    if not api_key:
        raise RuntimeError('OPENWEATHER_API_KEY is not configured.')

    params = {
        'lat': lat,
        'lon': lon,
        'appid': api_key,
    }

    try:
        response = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError('Failed to fetch weather data from OpenWeatherMap.') from exc

    payload = response.json()
    if 'list' not in payload or not isinstance(payload.get('list'), list) or not payload['list']:
        raise ValueError('Weather provider returned invalid forecast data.')

    return payload


def _extract_current_weather(forecast_payload):
    """Extract current weather snapshot from the first forecast entry."""
    current = forecast_payload['list'][0]
    main_data = current.get('main', {})
    weather_data = current.get('weather', [{}])
    wind_data = current.get('wind', {})

    rain_probability = int(round(float(current.get('pop', 0) or 0) * 100))

    return {
        'temp_c': _kelvin_to_celsius(main_data.get('temp')),
        'temperature': _kelvin_to_celsius(main_data.get('temp')),
        'humidity': int(main_data.get('humidity', 0) or 0),
        'condition': (weather_data[0].get('main', 'Unknown') if weather_data else 'Unknown').lower(),
        'wind_speed': round(float(wind_data.get('speed', 0) or 0), 2),
        'rain_probability': rain_probability,
    }


def _extract_forecast_date(item):
    """Return forecast date from dt timestamp (preferred) or dt_txt fallback."""
    dt_unix = item.get('dt')
    if dt_unix:
        return datetime.utcfromtimestamp(dt_unix).date()

    dt_text = item.get('dt_txt')
    if dt_text:
        return datetime.strptime(dt_text, '%Y-%m-%d %H:%M:%S').date()

    return None


def _build_five_day_forecast(forecast_payload):
    """Group 3-hour points into daily summaries for up to 5 days."""
    grouped = {}
    today = timezone.now().date()

    for item in forecast_payload.get('list', []):
        forecast_date = _extract_forecast_date(item)
        if not forecast_date or forecast_date < today:
            continue

        bucket = grouped.setdefault(
            forecast_date,
            {
                'temps': [],
                'rain_probabilities': [],
                'conditions': [],
            },
        )

        temp_kelvin = item.get('main', {}).get('temp')
        temp_c = _kelvin_to_celsius(temp_kelvin)
        if temp_c is not None:
            bucket['temps'].append(temp_c)

        pop_percent = int(round(float(item.get('pop', 0) or 0) * 100))
        bucket['rain_probabilities'].append(pop_percent)

        condition = (item.get('weather', [{}])[0].get('main', 'Unknown')).lower()
        bucket['conditions'].append(condition)

    daily_forecast = []
    for date_key in sorted(grouped.keys())[:WEATHER_FORECAST_DAYS]:
        day = grouped[date_key]
        if day['temps']:
            avg_temp = round(sum(day['temps']) / len(day['temps']), 2)
        else:
            avg_temp = None

        condition = 'unknown'
        if day['conditions']:
            condition = Counter(day['conditions']).most_common(1)[0][0]

        daily_forecast.append(
            {
                'date': date_key.isoformat(),
                'day_name': date_key.strftime('%a'),
                'avg_temp': avg_temp,
                'rain_probability': max(day['rain_probabilities']) if day['rain_probabilities'] else 0,
                'condition': condition,
            }
        )

    return daily_forecast


def _normalize_country_name(country_code):
    """Map ISO country code to a readable country name when available."""
    code = str(country_code or '').strip().upper()
    if not code:
        return ''
    return COUNTRY_NAME_OVERRIDES.get(code, code)


def _build_location_label(forecast_payload, lat, lon):
    """Return clean city + country only location string."""
    city_block = forecast_payload.get('city', {}) if isinstance(forecast_payload, dict) else {}
    city = str(city_block.get('name', '') or '').strip()
    country = _normalize_country_name(city_block.get('country'))

    parts = [part for part in [city, country] if part]
    if parts:
        return ', '.join(parts)

    return f'Lat {lat:.4f}, Lon {lon:.4f}'


def _dedupe_advice_items(advice_items):
    """Preserve order and remove duplicate advice messages."""
    deduped = []
    seen = set()

    for item in advice_items:
        message = str(item.get('message', '')).strip()
        category = item.get('category', 'other')
        if not message or message in seen:
            continue
        seen.add(message)
        deduped.append({'category': category, 'message': message})

    return deduped


def _build_advice_items(current_data):
    """Generate categorized smart farming advice messages."""
    advice_items = []

    temp_c = current_data.get('temp_c', current_data.get('temperature'))
    humidity = int(current_data.get('humidity', 0) or 0)
    condition = str(current_data.get('condition', '') or '').lower()
    wind_speed = float(current_data.get('wind_speed', 0) or 0)
    rain_probability = int(current_data.get('rain_probability', 0) or 0)

    if 'thunderstorm' in condition or 'storm' in condition:
        advice_items.append(
            {
                'category': 'rain',
                'message': '⛈️ Storm risk expected. Protect crops and avoid open-field operations.',
            }
        )

    if rain_probability > 60 or 'rain' in condition:
        advice_items.append({'category': 'rain', 'message': '🌧️ Rain expected — take precautions'})
    elif rain_probability >= 40:
        advice_items.append(
            {'category': 'other', 'message': '☔ Possible rain. Plan spraying and irrigation carefully.'}
        )

    if humidity > 80:
        advice_items.append(
            {
                'category': 'humidity',
                'message': '💦 High humidity. Monitor crops for disease pressure.',
            }
        )
    elif 70 <= humidity <= 80:
        advice_items.append(
            {'category': 'other', 'message': '🌫️ Moderate humidity. Keep field airflow and crop checks regular.'}
        )
    elif humidity < 45:
        advice_items.append({'category': 'other', 'message': '💧 Low humidity. Check soil moisture and irrigation timing.'})

    if temp_c is not None and (temp_c > 35 or temp_c < 15):
        if temp_c > 35:
            advice_items.append(
                {'category': 'temperature', 'message': '🔥 Extreme heat stress risk. Irrigate early and reduce midday work.'}
            )
        else:
            advice_items.append(
                {
                    'category': 'temperature',
                    'message': '❄️ Low temperature risk. Protect sensitive crops from cold stress.',
                }
            )
    elif temp_c is not None and 20 <= temp_c <= 30:
        advice_items.append({'category': 'other', 'message': '✅ Temperature is favorable for most crop activities.'})

    if wind_speed > 10:
        advice_items.append({'category': 'wind', 'message': '🌪️ Strong wind expected. Secure supports and young plants.'})
    elif 5 <= wind_speed <= 10:
        advice_items.append({'category': 'other', 'message': '🌬️ Moderate wind. Watch lightweight crops and structures.'})

    if 'clear' in condition:
        advice_items.append({'category': 'other', 'message': '☀️ Clear conditions. Good time for field operations.'})
    elif 'cloud' in condition:
        advice_items.append({'category': 'other', 'message': '☁️ Cloudy sky. Maintain routine crop monitoring.'})
    elif 'mist' in condition or 'fog' in condition:
        advice_items.append({'category': 'other', 'message': '🌫️ Mist/fog detected. Delay spraying until visibility improves.'})

    deduped_items = _dedupe_advice_items(advice_items)
    if not deduped_items:
        deduped_items.append({'category': 'other', 'message': '✅ Weather conditions are stable for farming.'})

    return deduped_items


def generate_advice(current_data):
    """Compatibility helper that returns plain advice string list."""
    return [item['message'] for item in _build_advice_items(current_data)]


def _prioritize_main_alert(advice_items, current_data):
    """Pick one highest-priority alert and return remaining advice."""
    condition = str(current_data.get('condition', '') or '').lower()
    rain_probability = int(current_data.get('rain_probability', 0) or 0)

    # Rain priority boost has absolute precedence.
    if rain_probability > 60 or 'rain' in condition:
        boosted_alert = '🌧️ Rain expected — take precautions'
        if not any(item.get('message') == boosted_alert for item in advice_items):
            advice_items = [{'category': 'rain', 'message': boosted_alert}] + list(advice_items)

        other_advice = [item['message'] for item in advice_items if item['message'] != boosted_alert]
        return boosted_alert, other_advice

    for category in ALERT_PRIORITY_ORDER:
        for item in advice_items:
            if item.get('category') == category:
                main_alert = item['message']
                other_advice = [candidate['message'] for candidate in advice_items if candidate['message'] != main_alert]
                return main_alert, other_advice

    fallback = '✅ Weather conditions are stable for farming.'
    return fallback, []


def build_today_summary(current_data, main_alert):
    """Generate a compact day summary with irrigation context."""
    humidity = int(current_data.get('humidity', 0) or 0)
    temperature = current_data.get('temperature')
    rain_probability = int(current_data.get('rain_probability', 0) or 0)
    condition = str(current_data.get('condition', '') or '').lower()

    if rain_probability > 60 or 'rain' in condition:
        irrigation_tip = 'Delay irrigation and prioritize drainage checks.'
    elif temperature is not None and float(temperature) > 35:
        irrigation_tip = 'Use early-morning irrigation to reduce heat stress.'
    elif humidity < 45:
        irrigation_tip = 'Increase irrigation slightly and monitor soil moisture.'
    elif humidity > 80:
        irrigation_tip = 'Avoid over-irrigation and improve crop airflow.'
    else:
        irrigation_tip = 'Keep routine irrigation based on soil moisture readings.'

    return f'{main_alert} {irrigation_tip}'


@require_http_methods(['GET'])
def weather_view(request):
    """Return optimized weather summary and 5-day forecast for coordinates."""
    lat_param = request.GET.get('lat')
    lon_param = request.GET.get('lon')

    try:
        lat = _parse_coordinate(lat_param, 'lat', -90, 90)
        lon = _parse_coordinate(lon_param, 'lon', -180, 180)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    cache_key = _weather_cache_key(lat, lon)
    cached_response = _cache_get_safe(cache_key)
    if cached_response:
        return JsonResponse(cached_response)

    try:
        forecast_payload = _fetch_openweather_forecast(lat, lon)
        current = _extract_current_weather(forecast_payload)
        forecast = _build_five_day_forecast(forecast_payload)
        advice_items = _build_advice_items(current)
        main_alert, other_advice = _prioritize_main_alert(advice_items, current)
        advice = [main_alert] + list(other_advice)
        location_label = _build_location_label(forecast_payload, lat, lon)
        today_summary = build_today_summary(current, main_alert)
    except RuntimeError as exc:
        logger.exception('Weather upstream error for lat=%s lon=%s', lat, lon)
        return JsonResponse({'error': str(exc)}, status=502)
    except ValueError as exc:
        logger.exception('Invalid weather payload for lat=%s lon=%s', lat, lon)
        return JsonResponse({'error': str(exc)}, status=502)
    except Exception:
        logger.exception('Unexpected weather API failure for lat=%s lon=%s', lat, lon)
        return JsonResponse({'error': 'Unexpected error while processing weather data.'}, status=500)

    response_payload = {
        'location': location_label,
        'temperature': current['temperature'],
        'humidity': current['humidity'],
        'condition': current['condition'],
        'wind_speed': current['wind_speed'],
        'rain_probability': current['rain_probability'],
        'main_alert': main_alert,
        'other_advice': other_advice,
        'today_summary': today_summary,
        # Backward-compatible fields.
        'temp_c': current['temperature'],
        'advice': advice,
        'current': {
            'temperature': current['temperature'],
            'temp_c': current['temperature'],
            'humidity': current['humidity'],
            'condition': current['condition'],
            'wind_speed': current['wind_speed'],
            'rain_probability': current['rain_probability'],
            'main_alert': main_alert,
            'other_advice': other_advice,
        },
        'alerts': advice,
        'forecast': forecast,
        'coordinates': {
            'lat': lat,
            'lon': lon,
        },
    }

    _cache_set_safe(cache_key, response_payload, WEATHER_CACHE_TTL_SECONDS)
    return JsonResponse(response_payload)


@require_http_methods(['GET'])
def weather_forecast_api(request):
    """Compatibility wrapper for existing route name."""
    return weather_view(request)


def is_farmer_approved(user):
    """Farmers have full access immediately."""
    return True


@login_required(login_url='login')
def farmer_dashboard(request):
    """Farmer dashboard"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    crops = Crop.objects.filter(farmer=request.user)
    orders = Order.objects.filter(farmer=request.user)
    pending_orders = orders.filter(status='pending')
    recent_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    unread_messages = recent_messages.filter(is_read=False).count()
    farmer_profile = FarmerProfile.objects.filter(user=request.user).first()
    
    context = {
        'crops': crops,
        'orders': orders,
        'recent_orders': orders.order_by('-order_date')[:5],
        'recent_crops': crops.order_by('-created_at')[:5],
        'pending_orders': pending_orders,
        'recent_messages': recent_messages,
        'unread_messages': unread_messages,
        'crops_count': crops.count(),
        'orders_count': orders.count(),
        'pending_orders_count': pending_orders.count(),
        'total_revenue': sum([order.total_price for order in orders.filter(status='delivered')]),
        'is_approved': is_farmer_approved(request.user),
        'farmer_profile': farmer_profile,
    }
    return render(request, 'farmer/dashboard.html', context)


@login_required(login_url='login')
def add_crop(request):
    """Add a new crop"""
    if request.user.role != 'farmer':
        messages.error(request, 'Only farmers can add crops!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.farmer = request.user
            crop.save()
            
            # Create crop listing
            CropListing.objects.create(crop=crop)
            
            messages.success(request, 'Crop added successfully!')
            return redirect('farmer_crops')
    else:
        # Prefill location from user's profile if available (user.location or farmer_profile.farm_location)
        default_loc = ''
        if getattr(request.user, 'location', None):
            default_loc = request.user.location
        else:
            try:
                farmer_profile = getattr(request.user, 'farmer_profile', None)
                if farmer_profile and getattr(farmer_profile, 'farm_location', None):
                    default_loc = farmer_profile.farm_location
            except Exception:
                default_loc = ''

        form = CropForm(initial={'location': default_loc})
    
    context = {'form': form, 'title': 'Add Crop'}
    return render(request, 'farmer/add_crop.html', context)


@login_required(login_url='login')
def edit_crop(request, crop_id):
    """Edit crop"""
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crop updated successfully!')
            return redirect('farmer_crops')
    else:
        form = CropForm(instance=crop)
    
    context = {'form': form, 'crop': crop, 'title': 'Edit Crop'}
    return render(request, 'farmer/edit_crop.html', context)


@login_required(login_url='login')
def delete_crop(request, crop_id):
    """Delete crop"""
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    crop.delete()
    messages.success(request, 'Crop deleted successfully!')
    return redirect('farmer_crops')


@login_required(login_url='login')
def farmer_crops(request):
    """View all farmer crops"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    crops = Crop.objects.filter(farmer=request.user).order_by('-created_at')
    
    context = {'crops': crops, 'title': 'My Crops'}
    return render(request, 'farmer/crops_list.html', context)


@login_required(login_url='login')
def farmer_orders(request):
    """View all orders for farmer's crops"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    orders = Order.objects.filter(farmer=request.user).order_by('-order_date')
    status_filter = request.GET.get('status')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'title': 'Orders Received',
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'farmer/orders_list.html', context)


@login_required(login_url='login')
def order_detail(request, order_id):
    """View order detail"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.user not in [order.farmer, order.buyer]:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    if request.method == 'POST' and request.user == order.farmer:
        new_status = request.POST.get('status')
        old_status = order.status
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            crop = order.crop
            
            # Deduct quantity when order is accepted
            if new_status == 'accepted' and old_status == 'pending':
                crop.deduct_quantity(order.quantity)
                if crop.quantity <= 0:
                    messages.info(request, f'{crop.crop_name} is now out of stock. It will be removed from marketplace in 24 hours if not restocked.')
            
            # Restore quantity if order is rejected or cancelled by farmer
            if new_status in ('rejected', 'cancelled') and old_status == 'accepted':
                crop.restore_quantity(order.quantity)
            
            # Send notification to buyer
            Notification.objects.create(
                user=order.buyer,
                notification_type='order',
                title=f'Order Update: {order.crop.crop_name}',
                message=f'Your order status has been updated to {new_status}'
            )
            messages.success(request, 'Order status updated!')
            return redirect('order_detail', order_id=order.id)
    
    context = {'order': order, 'title': 'Order Detail'}
    return render(request, 'farmer/order_detail.html', context)


@login_required(login_url='login')
def disease_result(request, disease_id):
    """Display disease detection result"""
    disease = get_object_or_404(CropDisease, id=disease_id)
    
    # Ensure user can only view their own results
    if disease.farmer != request.user and (disease.crop and disease.crop.farmer != request.user):
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('disease_detection')
    
    # Determine crop name
    if disease.crop and disease.crop.master_crop:
        crop_name = disease.crop.master_crop.crop_name
    elif disease.master_crop:
        crop_name = disease.master_crop.crop_name
    else:
        crop_name = 'Unknown Crop'
    
    context = {
        'disease': disease,
        'crop': disease.crop,
        'master_crop': disease.master_crop,
        'crop_name': crop_name,
        'title': 'Disease Detection Result'
    }
    return render(request, 'farmer/disease_result.html', context)


@login_required(login_url='login')
def disease_detection(request, crop_id=None):
    """AI Crop Disease Detection"""
    if request.user.role != 'farmer':
        messages.error(request, 'Only farmers can use disease detection!')
        return redirect('dashboard')
    
    # Only show crops that have master_crop assigned
    farmer_crops = Crop.objects.filter(farmer=request.user, master_crop__isnull=False).select_related('master_crop')
    # Master crops that admin allows farmers to analyze
    master_crops = MasterCrop.objects.filter(is_active=True, allow_detection=True)
    selected_crop = None
    selected_master_crop = None
    
    if request.method == 'POST':
        form = CropDiseaseForm(request.POST, request.FILES)
        selected_crop_id = request.POST.get('crop')
        selected_master_crop_id = request.POST.get('master_crop')

        # Prefer a farmer crop if provided, otherwise allow selecting a master crop type
        if selected_crop_id:
            selected_crop = get_object_or_404(Crop, id=selected_crop_id, farmer=request.user)
        elif selected_master_crop_id:
            selected_master_crop = get_object_or_404(MasterCrop, id=selected_master_crop_id, is_active=True, allow_detection=True)
        else:
            messages.error(request, 'Please select either one of your crops or an allowed crop type!')

        # If a crop/master_crop was chosen, proceed to analyze
        if selected_crop or selected_master_crop:
            image_file = request.FILES.get('disease_image')
            if image_file:
                try:
                    disease_info = analyze_disease_image(image_file)

                    # Create disease record; attach crop if a farmer listing was chosen,
                    # otherwise attach master_crop and record the farmer who requested the detection.
                    disease = CropDisease.objects.create(
                        crop=selected_crop if selected_crop else None,
                        master_crop=selected_master_crop if selected_master_crop else None,
                        farmer=request.user,
                        disease_name=disease_info.get('name', 'Unknown Disease'),
                        disease_type=disease_info.get('type', 'unknown'),
                        confidence_score=disease_info.get('confidence', 0),
                        disease_image=image_file,
                        treatment_recommendation=disease_info.get('treatment', ''),
                        ai_model_used=disease_info.get('model_used', 'plant_disease_model')
                    )

                    # Send notification
                    crop_name = selected_crop.master_crop.crop_name if selected_crop and selected_crop.master_crop else (selected_master_crop.crop_name if selected_master_crop else 'Unknown Crop')
                    Notification.objects.create(
                        user=request.user,
                        notification_type='disease',
                        title=f'Disease Detected: {disease.disease_name}',
                        message=f'Disease detected on {crop_name} with {disease.confidence_score:.1f}% confidence.'
                    )

                    messages.success(request, 'Disease analysis complete!')
                    # Redirect to result page
                    return redirect('disease_result', disease_id=disease.id)
                except Exception as e:
                    messages.error(request, f'Error analyzing image: {str(e)}')
                    detection_result = {'success': False, 'error': str(e)}
            else:
                messages.error(request, 'Please upload an image!')
    else:
        form = CropDiseaseForm()
    
    context = {
        'form': form,
        'crops': farmer_crops,
        'master_crops': master_crops,
        'selected_crop_id': crop_id,
        'title': 'AI Disease Detection'
    }
    return render(request, 'farmer/disease_detection.html', context)


@login_required(login_url='login')
def disease_history(request, crop_id):
    """View disease detection history"""
    crop = get_object_or_404(Crop, id=crop_id, farmer=request.user)
    diseases = crop.diseases.all().order_by('-detected_date')
    
    context = {
        'crop': crop,
        'diseases': diseases,
        'title': f'{crop.crop_name} - Disease History'
    }
    return render(request, 'farmer/disease_history.html', context)


@login_required(login_url='login')
def weather_alerts(request):
    """View real-time weather and disaster alerts"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    alerts = WeatherAlert.objects.filter(farmer=request.user, is_active=True).order_by('-created_at')

    try:
        initial_location = request.user.farmer_profile.farm_location or request.user.location or ''
    except Exception:
        initial_location = ''

    context = {
        'alerts': alerts,
        'openweather_api_key': getattr(settings, 'OPENWEATHER_API_KEY', '') or '',
        'initial_location': initial_location,
        'title': 'Weather & Disaster Forecast'
    }
    return render(request, 'farmer/weather_alerts.html', context)


@login_required(login_url='login')
def irrigation_module(request):
    """Render irrigation planning dashboard under Tools & Insights."""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    irrigation_crops = ensure_default_irrigation_crops(request.user)
    ensure_schedule_defaults(irrigation_crops)

    context = {
        'title': 'Irrigation Module',
        'irrigation_crops': irrigation_crops,
    }
    return render(request, 'farmer/irrigation_module.html', context)


@login_required(login_url='login')
@require_http_methods(['GET'])
def irrigation_crops_api(request):
    """Return farmer irrigation crops synced from active admin crop catalog."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    crops = ensure_default_irrigation_crops(request.user)

    payload = {
        'crops': [
            {
                'id': crop.id,
                'name': crop.name,
                'water_requirement': crop.water_requirement,
                'base_water_liters': float(crop.base_water_liters),
                'ideal_moisture': int(crop.ideal_moisture),
                'irrigation_frequency_days': int(crop.irrigation_frequency_days),
            }
            for crop in crops
        ]
    }
    return JsonResponse(payload)


def _parse_irrigation_crop_id(raw_value):
    try:
        crop_id = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError('crop_id is required and must be a valid integer.')

    if crop_id <= 0:
        raise ValueError('crop_id must be greater than zero.')

    return crop_id


@login_required(login_url='login')
@require_http_methods(['GET'])
def irrigation_plan_api(request):
    """Return smart irrigation plan based on live weather + crop profile."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    ensure_default_irrigation_crops(request.user)

    try:
        crop_id = _parse_irrigation_crop_id(request.GET.get('crop_id'))
        lat = _parse_coordinate(request.GET.get('lat'), 'lat', -90, 90)
        lon = _parse_coordinate(request.GET.get('lon'), 'lon', -180, 180)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    crop = get_object_or_404(IrrigationCrop, id=crop_id, farmer=request.user)

    try:
        forecast_payload = _fetch_openweather_forecast(lat, lon)
        current_weather = _extract_current_weather(forecast_payload)
        location_label = _build_location_label(forecast_payload, lat, lon)
    except RuntimeError as exc:
        logger.exception('Irrigation plan weather fetch failed for crop_id=%s', crop_id)
        return JsonResponse({'error': str(exc)}, status=502)
    except ValueError as exc:
        logger.exception('Irrigation plan invalid weather payload for crop_id=%s', crop_id)
        return JsonResponse({'error': str(exc)}, status=502)
    except Exception:
        logger.exception('Unexpected irrigation plan failure for crop_id=%s', crop_id)
        return JsonResponse({'error': 'Unexpected error while creating irrigation plan.'}, status=500)

    plan = generate_irrigation_plan(current_weather, crop)
    upsert_irrigation_schedule(crop, plan)

    response = {
        'location': location_label,
        'status': plan['status'],
        'irrigation_message': plan['irrigation_message'],
        'soil_moisture': plan['soil_moisture'],
        'soil_moisture_label': plan['soil_moisture_label'],
        'recommended_water_liters': plan['recommended_water_liters'],
        'decision_factors': plan['decision_factors'],
    }
    return JsonResponse(response)


@login_required(login_url='login')
@require_http_methods(['POST'])
def irrigation_log_api(request):
    """Save irrigation event and return updated usage summary."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    try:
        crop_id = _parse_irrigation_crop_id(payload.get('crop_id'))
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    crop = get_object_or_404(IrrigationCrop, id=crop_id, farmer=request.user)

    try:
        water_amount = float(payload.get('water_amount', 0))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'water_amount must be a number.'}, status=400)

    if water_amount <= 0:
        return JsonResponse({'error': 'water_amount must be greater than zero.'}, status=400)

    method = str(payload.get('method', 'manual') or 'manual').lower()
    if method not in dict(IrrigationRecord.METHOD_CHOICES):
        return JsonResponse({'error': 'method must be manual or automatic.'}, status=400)

    date_value = payload.get('date')
    if date_value:
        try:
            irrigation_date = datetime.strptime(str(date_value), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'date must be YYYY-MM-DD.'}, status=400)
    else:
        irrigation_date = timezone.localdate()

    record = IrrigationRecord.objects.create(
        crop=crop,
        date=irrigation_date,
        water_amount=round(water_amount, 2),
        method=method,
    )

    base_frequency = default_frequency_days_for_crop(crop)

    schedule, _ = IrrigationSchedule.objects.get_or_create(
        crop=crop,
        defaults={
            'next_irrigation_date': irrigation_date + timedelta(days=base_frequency),
            'frequency_days': base_frequency,
            'recommendation': 'Irrigation event logged. Continue monitoring weather.',
        },
    )
    schedule.next_irrigation_date = irrigation_date + timedelta(days=max(1, int(schedule.frequency_days)))
    schedule.recommendation = f'Irrigation logged on {irrigation_date.isoformat()}. Continue as scheduled.'
    schedule.save(update_fields=['next_irrigation_date', 'recommendation', 'updated_at'])

    summary = build_usage_summary(crop.irrigation_records.all())

    return JsonResponse(
        {
            'message': 'Irrigation event saved.',
            'record': {
                'id': record.id,
                'crop_id': crop.id,
                'crop_name': crop.name,
                'date': record.date.isoformat(),
                'water_amount': record.water_amount,
                'method': record.method,
            },
            'usage_summary': summary,
        },
        status=201,
    )


@login_required(login_url='login')
@require_http_methods(['GET'])
def irrigation_history_api(request):
    """Return irrigation event history and water usage stats."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    ensure_default_irrigation_crops(request.user)

    records = IrrigationRecord.objects.filter(crop__farmer=request.user).select_related('crop')
    crop_id_raw = request.GET.get('crop_id')
    if crop_id_raw:
        try:
            crop_id = _parse_irrigation_crop_id(crop_id_raw)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        records = records.filter(crop_id=crop_id)

    summary = build_usage_summary(records)

    per_crop_usage = [
        {
            'crop_id': row['crop_id'],
            'crop_name': row['crop__name'],
            'total_water_liters': round(float(row['total_water'] or 0), 2),
        }
        for row in records.values('crop_id', 'crop__name').annotate(total_water=Sum('water_amount')).order_by('-total_water')
    ]

    history_rows = [
        {
            'id': row.id,
            'crop_id': row.crop_id,
            'crop_name': row.crop.name,
            'date': row.date.isoformat(),
            'water_amount': row.water_amount,
            'method': row.method,
        }
        for row in records.order_by('-date', '-created_at')[:100]
    ]

    return JsonResponse(
        {
            'records': history_rows,
            'usage_summary': summary,
            'usage_by_crop': per_crop_usage,
        }
    )


@login_required(login_url='login')
@require_http_methods(['GET'])
def irrigation_schedule_api(request):
    """Return irrigation schedules and reminder state."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    crops = ensure_default_irrigation_crops(request.user)
    ensure_schedule_defaults(crops)

    schedules = IrrigationSchedule.objects.filter(crop__farmer=request.user).select_related('crop')
    crop_id_raw = request.GET.get('crop_id')
    if crop_id_raw:
        try:
            crop_id = _parse_irrigation_crop_id(crop_id_raw)
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        schedules = schedules.filter(crop_id=crop_id)

    today = timezone.localdate()
    serialized_schedules = []
    due_count = 0

    for schedule in schedules.order_by('next_irrigation_date'):
        is_due = schedule.next_irrigation_date <= today
        if is_due:
            due_count += 1

        serialized_schedules.append(
            {
                'crop_id': schedule.crop_id,
                'crop_name': schedule.crop.name,
                'next_irrigation_date': schedule.next_irrigation_date.isoformat(),
                'frequency_days': schedule.frequency_days,
                'recommendation': schedule.recommendation,
                'is_due': is_due,
            }
        )

    reminder = {
        'show': due_count > 0,
        'message': '⏰ Time to irrigate your crops' if due_count > 0 else '',
        'due_count': due_count,
    }

    return JsonResponse({'schedules': serialized_schedules, 'reminder': reminder})


@login_required(login_url='login')
def crop_price_prediction(request):
    """Render crop price prediction page with dropdown options."""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    from ai_models.price_prediction.predictor import get_dropdown_options
    options = get_dropdown_options()

    context = {
        'title': 'Crop Price Prediction',
        'commodities': options['commodities'],
        'varieties_json': json.dumps(options['varieties']),
        'markets': options['markets'],
    }
    return render(request, 'farmer/crop_price_prediction.html', context)


@login_required(login_url='login')
def price_predict_api(request):
    """AJAX endpoint: predict crop price for given inputs."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    commodity = data.get('commodity', '').strip()
    variety = data.get('variety', '').strip()
    market = data.get('market', '').strip()
    month = data.get('month')

    if not all([commodity, variety, market, month]):
        return JsonResponse({'error': 'All fields are required'}, status=400)

    try:
        month = int(month)
        if month < 1 or month > 12:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Month must be 1-12'}, status=400)

    import os
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    from ai_models.price_prediction.predictor import predict_price
    try:
        result = predict_price(commodity, variety, market, month)
    except ImportError as e:
        return JsonResponse({'error': f'Prediction service unavailable: {str(e)}'}, status=503)
    except FileNotFoundError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Prediction failed: {str(e)}'}, status=500)

    return JsonResponse(result)


@login_required(login_url='login')
def price_history_api(request):
    """AJAX endpoint: return historical price data for chart."""
    if request.user.role != 'farmer':
        return JsonResponse({'error': 'Access denied'}, status=403)

    commodity = request.GET.get('commodity', '').strip()
    variety = request.GET.get('variety', '').strip()
    market = request.GET.get('market', '').strip()

    if not all([commodity, variety, market]):
        return JsonResponse({'error': 'commodity, variety, market required'}, status=400)

    from ai_models.price_prediction.predictor import get_price_history
    history = get_price_history(commodity, variety, market)
    return JsonResponse({'history': history})


@login_required(login_url='login')
def messages_view(request):
    """View messages"""
    messages_list = Message.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user)
    ).order_by('-created_at')
    
    # Mark as read
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_read':
            message_id = request.POST.get('message_id')
            msg = get_object_or_404(Message, id=message_id)
            if msg.recipient == request.user:
                msg.is_read = True
                msg.save()
    
    context = {
        'messages': messages_list,
        'unread_count': messages_list.filter(recipient=request.user, is_read=False).count(),
        'title': 'Messages'
    }
    return render(request, 'farmer/messages.html', context)


@login_required(login_url='login')
def send_message(request, recipient_id):
    """Send message to a user"""
    recipient = get_object_or_404(CustomUser, id=recipient_id)
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.recipient = recipient
            message.save()
            
            # Create notification
            Notification.objects.create(
                user=recipient,
                notification_type='message',
                title=f'New message from {request.user.username}',
                message=form.cleaned_data.get('subject')
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('messages')
    else:
        form = MessageForm()
    
    context = {
        'form': form,
        'recipient': recipient,
        'title': f'Send Message to {recipient.username}'
    }
    return render(request, 'farmer/send_message.html', context)


@login_required(login_url='login')
def ratings_view(request):
    """View ratings received"""
    if request.user.role != 'farmer':
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    ratings = FarmerRating.objects.filter(farmer=request.user).order_by('-created_at')
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'ratings': ratings,
        'avg_rating': avg_rating,
        'total_ratings': ratings.count(),
        'title': 'My Ratings'
    }
    return render(request, 'farmer/ratings.html', context)
