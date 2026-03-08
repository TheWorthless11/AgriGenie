"""
Advanced Price Prediction using Random Forest Regressor
Incorporates historical price data, weather forecasts, and market trends
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)


class AdvancedPricePredictor:
    """
    Uses Random Forest Regressor with multiple features:
    - Historical price data (1 year)
    - Weather forecast (temperature, humidity, rainfall)
    - Seasonal patterns
    - Market trends
    - Day of week/month patterns
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = [
            'day_of_year', 'day_of_week', 'month',
            'price_lag_1', 'price_lag_7', 'price_lag_30',
            'price_mean_7d', 'price_std_7d',
            'temperature', 'humidity', 'rainfall',
            'seasonal_factor', 'trend'
        ]
    
    def prepare_features(self, prices, weather_data, date):
        """
        Prepare feature vector for prediction
        
        Args:
            prices: List of historical prices (last 30+ days)
            weather_data: Dict with temperature, humidity, rainfall
            date: Target prediction date
            
        Returns:
            Feature vector as numpy array
        """
        features = {}
        
        # Temporal features
        day_of_year = date.timetuple().tm_yday
        day_of_week = date.weekday()
        month = date.month
        
        features['day_of_year'] = day_of_year
        features['day_of_week'] = day_of_week
        features['month'] = month
        
        # Price lag features (past prices)
        prices_array = np.array(prices)
        if len(prices_array) > 0:
            features['price_lag_1'] = prices_array[-1] if len(prices_array) >= 1 else 0
            features['price_lag_7'] = prices_array[-7] if len(prices_array) >= 7 else prices_array[-1]
            features['price_lag_30'] = prices_array[-30] if len(prices_array) >= 30 else prices_array[-1]
            
            # Rolling statistics
            if len(prices_array) >= 7:
                features['price_mean_7d'] = np.mean(prices_array[-7:])
                features['price_std_7d'] = np.std(prices_array[-7:])
            else:
                features['price_mean_7d'] = np.mean(prices_array)
                features['price_std_7d'] = np.std(prices_array) if len(prices_array) > 1 else 0
        else:
            features['price_lag_1'] = 0
            features['price_lag_7'] = 0
            features['price_lag_30'] = 0
            features['price_mean_7d'] = 0
            features['price_std_7d'] = 0
        
        # Weather features
        features['temperature'] = weather_data.get('temperature', 25)
        features['humidity'] = weather_data.get('humidity', 60)
        features['rainfall'] = weather_data.get('rainfall', 0)
        
        # Seasonal factor (crops have seasonal price patterns)
        # Prices typically higher after harvest season
        seasonal_weights = {
            1: 1.1, 2: 1.15, 3: 1.2,   # Jan-Mar: Post-harvest high prices
            4: 1.0, 5: 0.9, 6: 0.8,     # Apr-Jun: Lower prices
            7: 0.75, 8: 0.7, 9: 0.8,    # Jul-Sep: Pre-harvest low
            10: 1.0, 11: 1.15, 12: 1.2  # Oct-Dec: Harvest season
        }
        features['seasonal_factor'] = seasonal_weights.get(month, 1.0)
        
        # Trend feature (price momentum)
        if len(prices_array) >= 7:
            recent_trend = (prices_array[-1] - prices_array[-7]) / prices_array[-7]
            features['trend'] = min(max(recent_trend, -0.5), 0.5)  # Clamp between -0.5 and 0.5
        else:
            features['trend'] = 0
        
        # Convert to ordered list matching feature_names
        feature_vector = [features.get(name, 0) for name in self.feature_names]
        return np.array(feature_vector).reshape(1, -1)
    
    def train_model(self, training_data):
        """
        Train Random Forest model with historical data
        
        Args:
            training_data: List of dicts with 'features' and 'price' keys
        """
        if len(training_data) < 10:
            logger.warning(f"Insufficient training data: {len(training_data)} samples")
            return False
        
        try:
            X = np.array([d['features'] for d in training_data])
            y = np.array([d['price'] for d in training_data])
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            # Log feature importance
            importances = self.model.feature_importances_
            for name, importance in zip(self.feature_names, importances):
                if importance > 0.05:
                    logger.info(f"Feature {name}: importance={importance:.4f}")
            
            return True
        except Exception as e:
            logger.error(f"Error training price prediction model: {e}")
            return False
    
    def predict(self, prices, weather_data, days_ahead=7):
        """
        Predict prices for next N days
        
        Args:
            prices: List of historical prices (last 30+ days)
            weather_data: List of weather forecasts for next N days
            days_ahead: Number of days to predict
            
        Returns:
            Dict with predictions and confidence
        """
        predictions = []
        current_date = datetime.now().date()
        current_prices = list(prices)
        
        try:
            for i in range(days_ahead):
                prediction_date = current_date + timedelta(days=i+1)
                
                # Get weather for this day
                if i < len(weather_data):
                    weather = weather_data[i]
                else:
                    # Use last available weather if forecast shorter than prediction days
                    weather = weather_data[-1] if weather_data else {
                        'temperature': 25,
                        'humidity': 60,
                        'rainfall': 0
                    }
                
                # Prepare features
                feature_vector = self.prepare_features(current_prices, weather, prediction_date)
                feature_vector_scaled = self.scaler.transform(feature_vector)
                
                # Predict
                if self.is_trained:
                    predicted_price = self.model.predict(feature_vector_scaled)[0]
                    
                    # Get prediction intervals from ensemble (std of tree predictions)
                    tree_predictions = np.array([
                        tree.predict(feature_vector_scaled)[0] 
                        for tree in self.model.estimators_
                    ])
                    confidence = 100 - min(np.std(tree_predictions) / predicted_price * 100, 50)
                else:
                    # Fallback if model not trained
                    predicted_price = current_prices[-1] if current_prices else 100
                    confidence = 50
                
                # Ensure reasonable bounds
                min_price = current_prices[-1] * 0.6 if current_prices else 0
                max_price = current_prices[-1] * 1.5 if current_prices else 999
                predicted_price = np.clip(predicted_price, min_price, max_price)
                
                predictions.append({
                    'date': prediction_date.isoformat(),
                    'price': float(predicted_price),
                    'confidence': float(max(min(confidence, 100), 0)),
                    'temperature': weather.get('temperature', 25),
                    'humidity': weather.get('humidity', 60),
                    'rainfall': weather.get('rainfall', 0)
                })
                
                # Update price history for next iteration (moving window)
                current_prices.append(predicted_price)
                if len(current_prices) > 30:
                    current_prices.pop(0)
            
            return {
                'status': 'success',
                'predictions': predictions,
                'model_confidence': float(np.mean([p['confidence'] for p in predictions]))
            }
        
        except Exception as e:
            logger.error(f"Error in price prediction: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'predictions': []
            }
    
    def get_feature_importance(self):
        """Get feature importance scores"""
        if not self.is_trained:
            return {}
        
        return {
            name: float(importance)
            for name, importance in zip(self.feature_names, self.model.feature_importances_)
        }


# Global predictor instance
_global_predictor = None


def get_price_predictor():
    """Get or create global predictor instance"""
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = AdvancedPricePredictor()
    return _global_predictor


def predict_prices_with_ml(crop, days_ahead=7):
    """
    Main function to predict crop prices using ML
    
    Args:
        crop: Crop instance
        days_ahead: Days to predict
        
    Returns:
        Dict with predictions
    """
    from farmer.models import CropPrice
    from ai_models.weather_service import WeatherService
    
    try:
        predictor = get_price_predictor()
        
        # Get historical prices (last 1 year)
        one_year_ago = datetime.now().date() - timedelta(days=365)
        price_history = CropPrice.objects.filter(
            crop=crop,
            prediction_date__gte=one_year_ago
        ).order_by('prediction_date').values_list('predicted_price', flat=True)
        
        prices = list(price_history) if price_history else [crop.price_per_unit]
        
        # Get weather forecast
        # Use farmer's location if available
        farmer_profile = crop.farmer.farmer_profile if hasattr(crop.farmer, 'farmer_profile') else None
        if farmer_profile and farmer_profile.latitude and farmer_profile.longitude:
            lat = farmer_profile.latitude
            lon = farmer_profile.longitude
        else:
            # Default to India center if no location
            lat, lon = 20.5937, 78.9629
        
        # Fetch weather forecast
        forecast_data = WeatherService.get_forecast(lat, lon, days=days_ahead)
        
        # Parse weather forecast
        weather_forecasts = []
        if forecast_data:
            for item in forecast_data.get('list', [])[:days_ahead]:
                weather_forecasts.append({
                    'temperature': item.get('main', {}).get('temp', 25),
                    'humidity': item.get('main', {}).get('humidity', 60),
                    'rainfall': item.get('rain', {}).get('3h', 0) if 'rain' in item else 0
                })
        
        # Fill missing forecast data with defaults
        while len(weather_forecasts) < days_ahead:
            weather_forecasts.append({
                'temperature': 25,
                'humidity': 60,
                'rainfall': 0
            })
        
        # Train model if not already trained
        if not predictor.is_trained and len(prices) >= 10:
            training_data = []
            for idx in range(10, len(prices)):
                feature_vector = predictor.prepare_features(
                    prices[:idx],
                    {'temperature': 25, 'humidity': 60, 'rainfall': 0},
                    datetime.now().date()
                )
                training_data.append({
                    'features': feature_vector[0],
                    'price': prices[idx]
                })
            predictor.train_model(training_data)
        
        # Make predictions
        result = predictor.predict(prices, weather_forecasts, days_ahead)
        
        return result
    
    except Exception as e:
        logger.error(f"Error in predict_prices_with_ml: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'predictions': []
        }
