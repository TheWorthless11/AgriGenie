"""
AI Models package for AgriGenie
Gracefully handles missing dependencies for development
"""

try:
    from .disease_detection import get_disease_detector, analyze_disease_image
except ImportError:
    # Fallback for development without ML libraries
    def analyze_disease_image(*args, **kwargs):
        return {
            'disease': 'Early Blight',
            'confidence': 0.85,
            'treatment': 'Use fungicides containing mancozeb or chlorothalonil',
            'is_mock': True
        }
    
    def get_disease_detector():
        return None

from .weather_service import WeatherService, get_coordinates_from_location, generate_weather_alert

__all__ = [
    'get_disease_detector',
    'analyze_disease_image',
    'WeatherService',
    'get_coordinates_from_location',
    'generate_weather_alert',
]
