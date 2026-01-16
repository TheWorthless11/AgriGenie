"""
Weather and climate utilities
"""

import requests
import json
from datetime import datetime, timedelta
from django.core.cache import cache
import os


class WeatherService:
    """
    Handles weather data and disaster alerts
    Uses OpenWeatherMap API (free tier)
    """
    
    API_KEY = os.getenv('WEATHER_API_KEY', 'demo_key')
    BASE_URL = 'https://api.openweathermap.org/data/2.5'
    
    # Disaster thresholds
    DISASTER_THRESHOLDS = {
        'flood': {
            'rain_mm': 50,  # Heavy rain causing potential flooding
            'alert_type': 'flood',
            'severity': 'high'
        },
        'drought': {
            'no_rain_days': 30,
            'alert_type': 'drought',
            'severity': 'medium'
        },
        'cyclone': {
            'wind_speed': 60,  # km/h
            'alert_type': 'cyclone',
            'severity': 'critical'
        },
        'frost': {
            'temp_celsius': 0,
            'alert_type': 'frost',
            'severity': 'high'
        },
        'heat_wave': {
            'temp_celsius': 40,
            'alert_type': 'heat_wave',
            'severity': 'high'
        }
    }
    
    @staticmethod
    def get_weather_data(latitude, longitude):
        """
        Fetch weather data for given location
        """
        try:
            cache_key = f'weather_{latitude}_{longitude}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            url = f"{WeatherService.BASE_URL}/weather"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': WeatherService.API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Cache for 30 minutes
                cache.set(cache_key, data, 60 * 30)
                return data
            else:
                return None
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return None
    
    @staticmethod
    def get_forecast(latitude, longitude, days=5):
        """
        Fetch weather forecast
        """
        try:
            cache_key = f'forecast_{latitude}_{longitude}'
            cached_data = cache.get(cache_key)
            
            if cached_data:
                return cached_data
            
            url = f"{WeatherService.BASE_URL}/forecast"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': WeatherService.API_KEY,
                'units': 'metric',
                'cnt': days * 8  # 5-day forecast with 3-hour intervals
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Cache for 2 hours
                cache.set(cache_key, data, 60 * 120)
                return data
            else:
                return None
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return None
    
    @staticmethod
    def check_disaster_alerts(weather_data, forecast_data):
        """
        Analyze weather data for potential disasters
        """
        alerts = []
        
        if not weather_data:
            return alerts
        
        # Check current conditions
        temp = weather_data.get('main', {}).get('temp', 0)
        wind_speed = weather_data.get('wind', {}).get('speed', 0) * 3.6  # m/s to km/h
        humidity = weather_data.get('main', {}).get('humidity', 0)
        
        # Frost alert
        if temp < 0:
            alerts.append({
                'type': 'frost',
                'severity': 'high',
                'message': f'Frost warning! Temperature is {temp}°C. Protect crops.',
                'recommendation': 'Cover sensitive crops or apply frost protection methods'
            })
        
        # Heat wave alert
        if temp > 40:
            alerts.append({
                'type': 'heat_wave',
                'severity': 'high',
                'message': f'Heat wave warning! Temperature is {temp}°C. Increase watering.',
                'recommendation': 'Provide adequate irrigation and shade if possible'
            })
        
        # Cyclone alert (high wind speed)
        if wind_speed > 60:
            alerts.append({
                'type': 'cyclone',
                'severity': 'critical',
                'message': f'High wind alert! Wind speed is {wind_speed} km/h.',
                'recommendation': 'Secure crops and protect from damage. Consider harvesting early.'
            })
        
        # Flood risk (high humidity + rain)
        rain = weather_data.get('rain', {}).get('1h', 0)
        if rain > 20 or (humidity > 90 and rain > 5):
            alerts.append({
                'type': 'flood',
                'severity': 'high',
                'message': f'Heavy rain detected! Rainfall: {rain}mm. Flood risk.',
                'recommendation': 'Ensure proper drainage and monitor water levels'
            })
        
        # Check forecast for upcoming disasters
        if forecast_data:
            forecast_list = forecast_data.get('list', [])
            for forecast_point in forecast_list[:8]:  # Check next 24 hours
                forecast_temp = forecast_point.get('main', {}).get('temp', 0)
                forecast_wind = forecast_point.get('wind', {}).get('speed', 0) * 3.6
                forecast_rain = forecast_point.get('rain', {}).get('3h', 0)
                
                # Drought warning (no rain for extended period - simulated)
                if forecast_rain == 0:
                    alerts.append({
                        'type': 'drought',
                        'severity': 'medium',
                        'message': 'Low rainfall expected in coming days. Monitor soil moisture.',
                        'recommendation': 'Plan irrigation schedules accordingly'
                    })
                    break
        
        return alerts
    
    @staticmethod
    def get_weather_summary(latitude, longitude):
        """
        Get complete weather summary for location
        """
        weather = WeatherService.get_weather_data(latitude, longitude)
        forecast = WeatherService.get_forecast(latitude, longitude)
        alerts = WeatherService.check_disaster_alerts(weather, forecast)
        
        if not weather:
            return None
        
        return {
            'location': weather.get('name', 'Unknown'),
            'temperature': weather.get('main', {}).get('temp', 0),
            'feels_like': weather.get('main', {}).get('feels_like', 0),
            'humidity': weather.get('main', {}).get('humidity', 0),
            'wind_speed': weather.get('wind', {}).get('speed', 0) * 3.6,
            'description': weather.get('weather', [{}])[0].get('main', 'Unknown'),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }


def get_coordinates_from_location(location_name):
    """
    Get latitude/longitude from location name using geocoding
    """
    try:
        url = 'https://nominatim.openstreetmap.org/search'
        params = {
            'q': location_name,
            'format': 'json',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    'latitude': float(data[0]['lat']),
                    'longitude': float(data[0]['lon']),
                    'display_name': data[0]['display_name']
                }
        return None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None


def generate_weather_alert(location, alert_type, severity):
    """
    Generate weather alert message
    """
    messages = {
        'flood': {
            'low': 'Light rain expected. Monitor water levels.',
            'medium': 'Moderate rain expected. Ensure proper drainage.',
            'high': 'Heavy rain warning! Prepare for potential flooding.',
            'critical': 'Severe flooding risk! Take immediate action!'
        },
        'drought': {
            'low': 'Low rainfall forecast. Increase irrigation.',
            'medium': 'Extended dry period expected. Plan water management.',
            'high': 'Severe drought warning. Critical irrigation needed.',
            'critical': 'Critical drought condition! Take emergency measures!'
        },
        'cyclone': {
            'low': 'Light winds forecast.',
            'medium': 'Strong winds expected. Secure loose structures.',
            'high': 'Severe wind warning! Protect crops immediately.',
            'critical': 'Cyclone warning! Seek shelter and protect assets!'
        },
        'frost': {
            'high': f'Frost alert for {location}! Protect sensitive crops.',
            'critical': f'Severe frost warning for {location}!'
        },
        'heat_wave': {
            'high': f'Heat wave alert for {location}! Increase watering.',
            'critical': f'Severe heat wave for {location}! Take urgent action!'
        }
    }
    
    return messages.get(alert_type, {}).get(severity, 'Weather alert issued')
