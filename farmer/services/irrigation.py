from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from farmer.models import IrrigationCrop, IrrigationCropCatalog, IrrigationSchedule


def _normalize_crop_name(value):
    return str(value or '').strip().lower()


def ensure_default_irrigation_crops(user):
    """Sync farmer crop profiles from active admin catalog and return active crops."""
    catalog_crops = list(IrrigationCropCatalog.objects.filter(is_active=True).order_by('name'))

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
                'water_requirement': catalog.water_requirement,
                'base_water_liters': catalog.base_water_liters,
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

    return {
        'name': crop_name or str(getattr(crop, 'name', 'crop')).strip().lower(),
        'water_need': water_need,
        'base_water_liters': float(getattr(crop, 'base_water_liters', 9.0) or 9.0),
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
    base_liters = float(crop_profile.get('base_water_liters', 9.0))

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


def generate_irrigation_plan(weather, crop):
    """Generate irrigation recommendation from weather, moisture simulation, and crop profile."""
    temp_c = float(weather.get('temp_c', weather.get('temperature', 0)) or 0)
    humidity = int(weather.get('humidity', 0) or 0)
    rain_probability = int(weather.get('rain_probability', 0) or 0)
    wind_speed = float(weather.get('wind_speed', 0) or 0)
    condition = str(weather.get('condition', '') or '').lower()
    crop_profile = get_crop_profile(crop)

    soil_moisture = estimate_soil_moisture(temp_c, humidity, rain_probability, wind_speed)
    soil_moisture_label = get_soil_moisture_label(soil_moisture)
    status, irrigation_message = determine_irrigation_status(soil_moisture, rain_probability, condition)
    rain_expected = _is_rain_expected(rain_probability, condition)

    frequency_days = calculate_frequency_days(weather, crop, status)
    recommended_water_liters = 0.0 if rain_expected else get_water_amount(crop, soil_moisture)

    next_irrigation_date = (
        timezone.localdate()
        if (status == 'URGENT' and not rain_expected)
        else (timezone.localdate() + timedelta(days=frequency_days))
    )

    decision_factors = []
    decision_factors.append('🌧️ Rain expected' if rain_expected else '🌤️ No rain expected')
    decision_factors.append(f'💧 {soil_moisture_label} soil moisture')

    if temp_c > 32:
        decision_factors.append('🔥 High temperature conditions')
    else:
        decision_factors.append('✅ Suitable temperature')

    decision_factors.append(f'🌱 {crop_profile["name"].title()} crop ({crop_profile["water_need"]} water need)')
    decision_factors.append(f'📅 Base frequency: every {crop_profile["irrigation_frequency_days"]} day(s)')

    return {
        'status': status,
        'irrigation_message': irrigation_message,
        'soil_moisture': soil_moisture,
        'soil_moisture_label': soil_moisture_label,
        'recommended_water_liters': recommended_water_liters,
        'next_irrigation_date': next_irrigation_date,
        'frequency_days': frequency_days,
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
