from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from farmer.models import Crop, IrrigationCrop, IrrigationCropCatalog, IrrigationSchedule
from farmer.services.irrigation_service import get_irrigation_recommendation


def _normalize_crop_name(value):
    return str(value or '').strip().lower()


def _latest_crop_area_map(user):
    """Return latest field-size values keyed by normalized crop name."""
    area_map = {}

    listings = Crop.objects.filter(farmer=user).select_related('master_crop').order_by('-updated_at', '-created_at')
    for listing in listings:
        if listing.master_crop_id:
            listing_name = _normalize_crop_name(getattr(listing.master_crop, 'crop_name', ''))
        else:
            listing_name = _normalize_crop_name(getattr(listing, 'crop_name', ''))

        if not listing_name or listing_name in area_map:
            continue

        area_map[listing_name] = {
            'area_size': float(getattr(listing, 'area_size', 1.0) or 1.0),
            'area_unit': str(getattr(listing, 'area_unit', 'm2') or 'm2').lower(),
        }

    return area_map


def ensure_default_irrigation_crops(user):
    """Sync farmer crop profiles from active admin catalog and return active crops."""
    catalog_crops = list(IrrigationCropCatalog.objects.filter(is_active=True).order_by('name'))
    latest_area_by_name = _latest_crop_area_map(user)

    if not catalog_crops:
        return IrrigationCrop.objects.none()

    active_names = []

    for catalog in catalog_crops:
        normalized_name = _normalize_crop_name(catalog.name)
        if not normalized_name:
            continue

        active_names.append(normalized_name)

        crop_obj, _ = IrrigationCrop.objects.get_or_create(
            farmer=user,
            name=normalized_name,
            defaults={
                'area_size': latest_area_by_name.get(normalized_name, {}).get('area_size', 1.0),
                'area_unit': latest_area_by_name.get(normalized_name, {}).get('area_unit', 'm2'),
                'water_requirement': catalog.water_requirement,
                'base_water_liters': catalog.base_water_liters,
                'water_per_m2': catalog.water_per_m2,
                'moisture_threshold': catalog.moisture_threshold,
                'retention_factor': catalog.retention_factor,
                'ideal_moisture': catalog.ideal_moisture,
                'irrigation_frequency_days': catalog.irrigation_frequency_days,
            },
        )

        changed_fields = []

        if crop_obj.water_requirement != catalog.water_requirement:
            crop_obj.water_requirement = catalog.water_requirement
            changed_fields.append('water_requirement')

        if float(crop_obj.base_water_liters) != float(catalog.base_water_liters):
            crop_obj.base_water_liters = catalog.base_water_liters
            changed_fields.append('base_water_liters')

        if float(crop_obj.water_per_m2) != float(catalog.water_per_m2):
            crop_obj.water_per_m2 = catalog.water_per_m2
            changed_fields.append('water_per_m2')

        if int(crop_obj.moisture_threshold) != int(catalog.moisture_threshold):
            crop_obj.moisture_threshold = catalog.moisture_threshold
            changed_fields.append('moisture_threshold')

        if float(crop_obj.retention_factor) != float(catalog.retention_factor):
            crop_obj.retention_factor = catalog.retention_factor
            changed_fields.append('retention_factor')

        if int(crop_obj.ideal_moisture) != int(catalog.ideal_moisture):
            crop_obj.ideal_moisture = catalog.ideal_moisture
            changed_fields.append('ideal_moisture')

        if int(crop_obj.irrigation_frequency_days) != int(catalog.irrigation_frequency_days):
            crop_obj.irrigation_frequency_days = catalog.irrigation_frequency_days
            changed_fields.append('irrigation_frequency_days')

        if changed_fields:
            changed_fields.append('updated_at')
            crop_obj.save(update_fields=changed_fields)

    if not active_names:
        return IrrigationCrop.objects.none()

    return IrrigationCrop.objects.filter(farmer=user, name__in=active_names).order_by('name')


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def get_crop_profile(crop):
    """Return normalized crop profile sourced from database-backed crop settings."""
    crop_name = _normalize_crop_name(getattr(crop, 'name', ''))
    water_need = str(getattr(crop, 'water_requirement', 'medium') or 'medium').lower()
    if water_need not in {'low', 'medium', 'high'}:
        water_need = 'medium'

    area_size = float(getattr(crop, 'area_size', 1.0) or 1.0)
    area_unit = str(getattr(crop, 'area_unit', 'm2') or 'm2').lower()
    area_m2 = float(getattr(crop, 'area_size_m2', area_size))

    return {
        'name': crop_name or str(getattr(crop, 'name', 'crop')).strip().lower(),
        'water_need': water_need,
        'area_size': round(max(area_size, 0.01), 2),
        'area_unit': area_unit,
        'area_m2': round(max(area_m2, 0.01), 2),
        'base_water_liters': float(getattr(crop, 'base_water_liters', 9.0) or 9.0),
        'water_per_m2': round(max(float(getattr(crop, 'water_per_m2', 2.0) or 2.0), 0.0), 3),
        'moisture_threshold': int(_clamp(int(getattr(crop, 'moisture_threshold', 45) or 45), 0, 100)),
        'retention_factor': round(max(float(getattr(crop, 'retention_factor', 0.5) or 0.5), 0.0), 3),
        'ideal_moisture': int(_clamp(int(getattr(crop, 'ideal_moisture', 60) or 60), 0, 100)),
        'irrigation_frequency_days': int(
            _clamp(int(getattr(crop, 'irrigation_frequency_days', 3) or 3), 1, 30)
        ),
    }


def estimate_soil_moisture(temp_c, humidity, rain_probability, wind_speed):
    """Estimate soil moisture using weather-aware simulation model."""
    moisture = (
        float(humidity)
        + (float(rain_probability) * 0.3)
        - (float(temp_c) * 0.4)
        - (float(wind_speed) * 0.2)
    )
    return round(_clamp(moisture, 0.0, 100.0), 1)


def get_soil_moisture_label(soil_moisture):
    """Convert numeric soil moisture into a farmer-friendly level."""
    if soil_moisture < 40:
        return 'Low'
    if soil_moisture <= 60:
        return 'Moderate'
    return 'High'


def _is_rain_expected(rain_probability, condition):
    normalized_condition = str(condition or '').lower()
    return float(rain_probability) > 60 or 'rain' in normalized_condition


def determine_irrigation_status(soil_moisture, rain_probability, condition):
    """Return irrigation status and primary message from moisture and weather."""
    if _is_rain_expected(rain_probability, condition):
        return 'SAFE', '🌧️ Rain expected. Skip irrigation.'

    if soil_moisture < 40:
        return 'URGENT', '🔥 Soil is very dry. Irrigate immediately.'

    if 40 <= soil_moisture <= 60:
        return 'MODERATE', '🌤️ Soil moisture is moderate. Irrigation needed soon.'

    return 'SAFE', '✅ Soil moisture is sufficient. No immediate irrigation needed.'


def get_water_amount(crop, soil_moisture):
    """Return recommended irrigation water amount in liters."""
    crop_profile = get_crop_profile(crop)
    base_liters = float(crop_profile.get('water_per_m2', 2.0)) * float(crop_profile.get('area_m2', 1.0))

    if soil_moisture < 40:
        base_liters *= 1.3
    elif soil_moisture > 70:
        base_liters *= 0.7

    return round(max(base_liters, 0.0), 2)


def default_frequency_days_for_crop(crop):
    """Return baseline irrigation frequency from crop profile configuration."""
    return get_crop_profile(crop)['irrigation_frequency_days']


def calculate_frequency_days(weather, crop, status):
    """Calculate dynamic irrigation frequency based on weather and status."""
    temp_c = float(weather.get('temp_c', weather.get('temperature', 0)) or 0)
    rain_probability = int(weather.get('rain_probability', 0) or 0)
    condition = str(weather.get('condition', '') or '').lower()
    base_frequency = default_frequency_days_for_crop(crop)

    if status == 'URGENT':
        frequency_days = max(1, base_frequency - 1)
    elif status == 'MODERATE':
        frequency_days = base_frequency
    else:
        frequency_days = base_frequency + 1

    if temp_c > 32 and not _is_rain_expected(rain_probability, condition):
        frequency_days = max(1, frequency_days - 1)
    elif temp_c < 18 and status == 'SAFE':
        frequency_days += 1

    if _is_rain_expected(rain_probability, condition):
        frequency_days += 2

    return int(_clamp(frequency_days, 1, 30))


def _status_from_memory_recommendation(action, effective_moisture, moisture_threshold):
    if action == 'irrigate':
        if effective_moisture <= max(0.0, moisture_threshold - 10.0):
            return 'URGENT'
        return 'MODERATE'
    return 'SAFE'


def generate_irrigation_plan(weather, crop, user=None):
    """Generate irrigation recommendation from weather, crop profile, and irrigation memory."""
    temp_c = float(weather.get('temp_c', weather.get('temperature', 0)) or 0)
    humidity = int(weather.get('humidity', 0) or 0)
    rain_probability = int(weather.get('rain_probability', 0) or 0)
    wind_speed = float(weather.get('wind_speed', 0) or 0)
    condition = str(weather.get('condition', '') or '').lower()

    base_soil_moisture = estimate_soil_moisture(temp_c, humidity, rain_probability, wind_speed)
    crop_profile = get_crop_profile(crop)

    recommendation = get_irrigation_recommendation(
        user=user,
        crop=crop,
        weather_data=weather,
        soil_moisture=base_soil_moisture,
    )

    action = str(recommendation.get('action', 'no_irrigation') or 'no_irrigation').lower()
    reason = str(recommendation.get('reason', 'optimal') or 'optimal').lower()
    irrigation_message = str(recommendation.get('message', '') or 'Soil moisture is sufficient')

    moisture_threshold = float(recommendation.get('moisture_threshold', 45.0) or 45.0)
    effective_soil_moisture = float(recommendation.get('effective_moisture', base_soil_moisture) or base_soil_moisture)
    soil_moisture = round(_clamp(effective_soil_moisture, 0.0, 100.0), 1)
    soil_moisture_label = get_soil_moisture_label(soil_moisture)
    status = _status_from_memory_recommendation(action, soil_moisture, moisture_threshold)

    rain_expected = bool(recommendation.get('rain_expected', _is_rain_expected(rain_probability, condition)))
    next_irrigation_in_hours = recommendation.get('next_irrigation_in_hours')
    area_m2 = float(recommendation.get('area_m2', crop_profile.get('area_m2', 1.0)) or crop_profile.get('area_m2', 1.0))
    water_per_m2 = float(recommendation.get('water_per_m2', crop_profile.get('water_per_m2', 2.0)) or crop_profile.get('water_per_m2', 2.0))
    recommendation_formula = str(recommendation.get('recommendation_formula', '') or '')

    try:
        next_irrigation_in_hours = max(0.0, float(next_irrigation_in_hours))
    except (TypeError, ValueError):
        next_irrigation_in_hours = None

    frequency_days = calculate_frequency_days(weather, crop, status)
    recommended_water_liters = float(recommendation.get('recommended_water_liters', 0.0) or 0.0)
    if action != 'irrigate':
        recommended_water_liters = 0.0

    if status == 'URGENT' and not rain_expected and (next_irrigation_in_hours is None or next_irrigation_in_hours <= 0):
        next_irrigation_date = timezone.localdate()
    elif next_irrigation_in_hours is not None:
        next_irrigation_date = (timezone.now() + timedelta(hours=next_irrigation_in_hours)).date()
    else:
        next_irrigation_date = timezone.localdate() + timedelta(days=frequency_days)

    decision_factors = []
    if recommendation.get('last_irrigation_at'):
        hours_ago = recommendation.get('last_irrigation_hours_ago')
        if hours_ago is None:
            decision_factors.append('🧠 Last irrigation history is available')
        else:
            decision_factors.append(f'🧠 Last irrigation was {float(hours_ago):.1f} hour(s) ago')
    else:
        decision_factors.append('🧠 No irrigation history yet')

    decision_factors.append('🌧️ Rain expected' if rain_expected else '🌤️ No rain expected')
    decision_factors.append(f'💧 Effective soil moisture: {soil_moisture:.1f}%')
    decision_factors.append(f'🎯 Moisture threshold: {moisture_threshold:.1f}%')
    decision_factors.append(f'📐 Field size: {area_m2:.2f} m²')
    decision_factors.append(f'💦 Water rate: {water_per_m2:.2f} L/m²')

    if temp_c > 32:
        decision_factors.append('🔥 High temperature conditions')
    else:
        decision_factors.append('✅ Suitable temperature')

    decision_factors.append(f'🌱 {crop_profile["name"].title()} crop ({crop_profile["water_need"]} water need)')
    decision_factors.append(f'📅 Base frequency: every {crop_profile["irrigation_frequency_days"]} day(s)')

    if reason == 'recent_irrigation':
        decision_factors.append('⏱️ Recent irrigation memory is active')

    if recommendation_formula:
        decision_factors.append(f'🧮 {recommendation_formula}')

    return {
        'action': action,
        'reason': reason,
        'status': status,
        'irrigation_message': irrigation_message,
        'message': irrigation_message,
        'soil_moisture': soil_moisture,
        'soil_moisture_label': soil_moisture_label,
        'raw_soil_moisture': round(base_soil_moisture, 1),
        'effective_soil_moisture': soil_moisture,
        'moisture_threshold': round(moisture_threshold, 1),
        'recommended_water_liters': recommended_water_liters,
        'water_per_m2': round(water_per_m2, 3),
        'area_m2': round(area_m2, 2),
        'recommendation_formula': recommendation_formula,
        'next_irrigation_date': next_irrigation_date,
        'next_irrigation_in_hours': next_irrigation_in_hours,
        'frequency_days': frequency_days,
        'last_irrigation_at': recommendation.get('last_irrigation_at'),
        'memory_factor': recommendation.get('memory_factor'),
        'retention_factor': recommendation.get('retention_factor', recommendation.get('memory_factor')),
        'decision_factors': decision_factors,
    }


def upsert_irrigation_schedule(crop, plan):
    """Persist the latest schedule suggestion for a crop."""
    return IrrigationSchedule.objects.update_or_create(
        crop=crop,
        defaults={
            'next_irrigation_date': plan['next_irrigation_date'],
            'frequency_days': plan['frequency_days'],
            'recommendation': plan['irrigation_message'],
        },
    )[0]


def ensure_schedule_defaults(crop_queryset):
    """Create baseline schedules so reminder/schedule APIs are never empty."""
    today = timezone.localdate()
    for crop in crop_queryset:
        base_frequency = default_frequency_days_for_crop(crop)
        IrrigationSchedule.objects.get_or_create(
            crop=crop,
            defaults={
                'next_irrigation_date': today + timedelta(days=base_frequency),
                'frequency_days': base_frequency,
                'recommendation': '✅ Stable weather. Follow regular irrigation schedule.',
            },
        )


def build_usage_summary(records_queryset):
    """Build daily and weekly usage summaries for dashboards and APIs."""
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    daily_usage = (
        records_queryset.filter(date=today).aggregate(total=Sum('water_amount')).get('total')
        or 0.0
    )
    weekly_usage = (
        records_queryset.filter(date__gte=week_start, date__lte=today).aggregate(total=Sum('water_amount')).get('total')
        or 0.0
    )
    total_usage = records_queryset.aggregate(total=Sum('water_amount')).get('total') or 0.0

    daily_breakdown = [
        {
            'date': row['date'].isoformat(),
            'water_amount': round(float(row['total'] or 0.0), 2),
        }
        for row in records_queryset.filter(date__gte=week_start, date__lte=today)
        .values('date')
        .annotate(total=Sum('water_amount'))
        .order_by('date')
    ]

    return {
        'daily_usage_liters': round(float(daily_usage), 2),
        'weekly_usage_liters': round(float(weekly_usage), 2),
        'total_usage_liters': round(float(total_usage), 2),
        'daily_breakdown': daily_breakdown,
    }
