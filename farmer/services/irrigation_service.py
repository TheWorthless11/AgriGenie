from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from farmer.models import AREA_TO_M2_FACTOR, IrrigationRecord


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _resolve_recent_window_hours():
    configured_hours = _safe_float(getattr(settings, 'IRRIGATION_RECENT_WINDOW_HOURS', 6), 6)
    return _clamp(configured_hours, 1.0, 24.0)


def convert_to_m2(area_size, area_unit):
    unit = str(area_unit or 'm2').strip().lower()
    factor = _safe_float(AREA_TO_M2_FACTOR.get(unit, 1.0), 1.0)
    normalized_size = max(0.0, _safe_float(area_size, 0.0))
    return round(normalized_size * factor, 2)


def _resolve_area_m2(crop):
    return max(0.01, convert_to_m2(getattr(crop, 'area_size', 1.0), getattr(crop, 'area_unit', 'm2')))


def _resolve_retention_factor(crop):
    return _clamp(
        _safe_float(getattr(crop, 'retention_factor', getattr(settings, 'IRRIGATION_MEMORY_FACTOR', 0.5)), 0.5),
        0.0,
        2.5,
    )


def _resolve_water_per_m2(crop, weather_data, rain_expected):
    base_water_per_m2 = _clamp(
        _safe_float(getattr(crop, 'water_per_m2', getattr(settings, 'IRRIGATION_DEFAULT_WATER_PER_M2', 2.0)), 2.0),
        0.0,
        20.0,
    )

    if rain_expected:
        return base_water_per_m2

    temp_c = _safe_float(weather_data.get('temp_c', weather_data.get('temperature', 0)), 0)
    high_temp_threshold = _safe_float(getattr(settings, 'IRRIGATION_HIGH_TEMP_THRESHOLD_C', 32), 32)
    high_temp_boost = _safe_float(getattr(settings, 'IRRIGATION_HIGH_TEMP_WATER_BOOST', 0.1), 0.1)

    if temp_c >= high_temp_threshold:
        return round(base_water_per_m2 * (1.0 + max(0.0, high_temp_boost)), 3)

    return round(base_water_per_m2, 3)


def _resolve_moisture_threshold(crop):
    direct_threshold = _safe_float(getattr(crop, 'moisture_threshold', 0), 0)
    if direct_threshold > 0:
        return _clamp(round(direct_threshold, 1), 20.0, 85.0)

    default_threshold = _safe_float(getattr(settings, 'IRRIGATION_MOISTURE_THRESHOLD', 45.0), 45.0)
    ideal_moisture = _safe_float(getattr(crop, 'ideal_moisture', 0), 0)
    if ideal_moisture > 0:
        return _clamp(round(ideal_moisture * 0.8, 1), 20.0, 85.0)
    return _clamp(default_threshold, 20.0, 85.0)


def _is_rain_expected(weather_data):
    weather_data = weather_data or {}
    rain_probability = int(round(_safe_float(weather_data.get('rain_probability', 0), 0)))
    condition = str(weather_data.get('condition', '') or '').lower()
    rain_threshold = int(round(_safe_float(getattr(settings, 'IRRIGATION_RAIN_PROBABILITY_THRESHOLD', 60), 60)))

    rain_keywords = ('rain', 'storm', 'drizzle', 'shower', 'thunder')
    return rain_probability >= rain_threshold or any(keyword in condition for keyword in rain_keywords)


def _evaporation_rate_per_hour(weather_data):
    weather_data = weather_data or {}

    temp_c = _safe_float(weather_data.get('temp_c', weather_data.get('temperature', 28)), 28)
    humidity = _safe_float(weather_data.get('humidity', 60), 60)
    wind_speed = _safe_float(weather_data.get('wind_speed', 0), 0)

    # Approximate moisture depletion rate in percentage points per hour.
    base_rate = 0.8
    temp_component = max(0.0, temp_c - 22.0) * 0.09
    humidity_component = max(0.0, 55.0 - humidity) * 0.02
    wind_component = max(0.0, wind_speed) * 0.03

    return _clamp(base_rate + temp_component + humidity_component + wind_component, 0.4, 4.0)


def _recommended_water_liters(area_m2, water_per_m2, effective_moisture, moisture_threshold):
    deficit = max(0.0, moisture_threshold - effective_moisture)
    if deficit <= 0:
        return 0.0

    deficit_multiplier = 1.0 + min(0.5, deficit / 40.0)
    return round(max(0.5, area_m2 * water_per_m2 * deficit_multiplier), 2)


def _get_last_irrigation(user, crop):
    if not user or not crop:
        return None

    latest = IrrigationRecord.objects.filter(user=user, crop=crop).order_by('-created_at').first()
    if latest:
        return latest

    return IrrigationRecord.objects.filter(crop=crop, crop__farmer=user).order_by('-created_at').first()


def _predict_next_irrigation_hours(
    last_irrigation,
    weather_data,
    effective_moisture,
    moisture_threshold,
    area_m2,
    retention_factor,
):
    evaporation_rate = _evaporation_rate_per_hour(weather_data)
    now = timezone.now()

    projected_moisture = _clamp(_safe_float(effective_moisture, 0.0), 0.0, 100.0)
    if projected_moisture <= moisture_threshold:
        return 0.0

    hours_to_threshold = (projected_moisture - moisture_threshold) / evaporation_rate

    if last_irrigation and getattr(last_irrigation, 'created_at', None):
        liters_per_m2 = _safe_float(last_irrigation.water_amount, 0.0) / max(0.01, area_m2)
        persistence_bonus = liters_per_m2 * max(0.0, retention_factor)
        hours_to_threshold += persistence_bonus / max(0.1, evaporation_rate)

        elapsed = max(0.0, (now - last_irrigation.created_at).total_seconds() / 3600.0)
        hours_to_threshold = max(0.0, hours_to_threshold - elapsed)

    return round(_clamp(hours_to_threshold, 0.0, 168.0), 1)


def _formula_text(water_per_m2, area_m2, total_water):
    base_total = max(0.0, _safe_float(water_per_m2, 0.0) * _safe_float(area_m2, 0.0))
    total = max(0.0, _safe_float(total_water, 0.0))

    if base_total <= 0.0 or abs(total - base_total) < 0.01:
        return f"Recommended: {water_per_m2:.2f} L/m² × {area_m2:.2f} m² = {total:.2f} L"

    moisture_factor = max(1.0, total / base_total)
    return (
        f"Recommended: {water_per_m2:.2f} L/m² × {area_m2:.2f} m² × "
        f"{moisture_factor:.2f} (deficit factor) = {total:.2f} L"
    )


def get_irrigation_recommendation(user, crop, weather_data, soil_moisture):
    """Return memory-aware irrigation recommendation for a user and crop."""
    weather_data = weather_data or {}
    now = timezone.now()

    base_soil_moisture = _clamp(_safe_float(soil_moisture, 0.0), 0.0, 100.0)
    area_m2 = _resolve_area_m2(crop)
    moisture_threshold = _resolve_moisture_threshold(crop)
    retention_factor = _resolve_retention_factor(crop)

    last_irrigation = _get_last_irrigation(user=user, crop=crop)
    last_irrigation_at = None
    last_irrigation_hours_ago = None
    memory_boost = 0.0

    if last_irrigation:
        last_irrigation_at = last_irrigation.created_at.isoformat() if last_irrigation.created_at else None
        if last_irrigation.created_at:
            last_irrigation_hours_ago = round(max(0.0, (now - last_irrigation.created_at).total_seconds() / 3600.0), 2)
        memory_boost = max(0.0, (_safe_float(last_irrigation.water_amount, 0.0) / area_m2) * retention_factor)

    effective_moisture = _clamp(base_soil_moisture + memory_boost, 0.0, 100.0)
    rain_expected = _is_rain_expected(weather_data)
    water_per_m2 = _resolve_water_per_m2(crop, weather_data, rain_expected)

    next_irrigation_in_hours = _predict_next_irrigation_hours(
        last_irrigation=last_irrigation,
        weather_data=weather_data,
        effective_moisture=effective_moisture,
        moisture_threshold=moisture_threshold,
        area_m2=area_m2,
        retention_factor=retention_factor,
    )

    recent_window_hours = _resolve_recent_window_hours()

    if last_irrigation and last_irrigation.created_at:
        if (now - last_irrigation.created_at) <= timedelta(hours=recent_window_hours):
            remaining_recent_window = max(0.0, round(recent_window_hours - (last_irrigation_hours_ago or 0.0), 1))
            next_irrigation_in_hours = max(next_irrigation_in_hours, remaining_recent_window)
            formula_text = _formula_text(water_per_m2, area_m2, 0.0)

            return {
                'action': 'no_irrigation',
                'message': 'Recently irrigated',
                'reason': 'recent_irrigation',
                'recommended_water_liters': 0.0,
                'water_per_m2': water_per_m2,
                'area_m2': round(area_m2, 2),
                'recommendation_formula': formula_text,
                'next_irrigation_in_hours': next_irrigation_in_hours,
                'effective_moisture': round(effective_moisture, 1),
                'soil_moisture': round(base_soil_moisture, 1),
                'moisture_threshold': round(moisture_threshold, 1),
                'memory_factor': round(retention_factor, 3),
                'retention_factor': round(retention_factor, 3),
                'last_irrigation_at': last_irrigation_at,
                'last_irrigation_hours_ago': last_irrigation_hours_ago,
                'rain_expected': rain_expected,
            }

    if rain_expected:
        formula_text = _formula_text(water_per_m2, area_m2, 0.0)
        return {
            'action': 'no_irrigation',
            'message': 'Rain expected, skip irrigation',
            'reason': 'rain_expected',
            'recommended_water_liters': 0.0,
            'water_per_m2': water_per_m2,
            'area_m2': round(area_m2, 2),
            'recommendation_formula': formula_text,
            'next_irrigation_in_hours': next_irrigation_in_hours,
            'effective_moisture': round(effective_moisture, 1),
            'soil_moisture': round(base_soil_moisture, 1),
            'moisture_threshold': round(moisture_threshold, 1),
            'memory_factor': round(retention_factor, 3),
            'retention_factor': round(retention_factor, 3),
            'last_irrigation_at': last_irrigation_at,
            'last_irrigation_hours_ago': last_irrigation_hours_ago,
            'rain_expected': True,
        }

    if effective_moisture < moisture_threshold:
        total_water = _recommended_water_liters(
            area_m2=area_m2,
            water_per_m2=water_per_m2,
            effective_moisture=effective_moisture,
            moisture_threshold=moisture_threshold,
        )
        formula_text = _formula_text(water_per_m2, area_m2, total_water)
        return {
            'action': 'irrigate',
            'message': 'Irrigate your field',
            'reason': 'low_moisture',
            'recommended_water_liters': total_water,
            'water_per_m2': water_per_m2,
            'area_m2': round(area_m2, 2),
            'recommendation_formula': formula_text,
            'next_irrigation_in_hours': 0.0,
            'effective_moisture': round(effective_moisture, 1),
            'soil_moisture': round(base_soil_moisture, 1),
            'moisture_threshold': round(moisture_threshold, 1),
            'memory_factor': round(retention_factor, 3),
            'retention_factor': round(retention_factor, 3),
            'last_irrigation_at': last_irrigation_at,
            'last_irrigation_hours_ago': last_irrigation_hours_ago,
            'rain_expected': False,
        }

    formula_text = _formula_text(water_per_m2, area_m2, 0.0)
    return {
        'action': 'no_irrigation',
        'message': 'Soil moisture is sufficient',
        'reason': 'optimal',
        'recommended_water_liters': 0.0,
        'water_per_m2': water_per_m2,
        'area_m2': round(area_m2, 2),
        'recommendation_formula': formula_text,
        'next_irrigation_in_hours': next_irrigation_in_hours,
        'effective_moisture': round(effective_moisture, 1),
        'soil_moisture': round(base_soil_moisture, 1),
        'moisture_threshold': round(moisture_threshold, 1),
        'memory_factor': round(retention_factor, 3),
        'retention_factor': round(retention_factor, 3),
        'last_irrigation_at': last_irrigation_at,
        'last_irrigation_hours_ago': last_irrigation_hours_ago,
        'rain_expected': False,
    }
