"""
AI/ML utilities for crop price prediction
Mock implementation for development
"""

import json
from datetime import datetime, timedelta
import random


class PricePredictionModel:
    """
    Handles crop price prediction using time-series analysis
    """
    
    def __init__(self):
        self.is_mock = True
    
    def generate_price_trend(self, current_price, days_ahead=30, volatility=0.05):
        """
        Generate price trend for next N days
        
        Args:
            current_price: Current crop price
            days_ahead: Number of days to predict
            volatility: Price volatility factor (0-1)
        
        Returns:
            List of predicted prices with dates
        """
        predictions = []
        current_date = datetime.now().date()
        current = float(current_price)
        
        # Generate realistic price variations
        for i in range(days_ahead):
            date = current_date + timedelta(days=i)
            
            # Seasonal trend (prices tend to increase after harvest)
            seasonal_factor = 1 + (random.uniform(-0.1, 0.1))
            
            # Random walk with drift
            random_change = random.uniform(-volatility, volatility)
            
            # Market trend
            trend = 1 + (i / days_ahead * 0.05)
            
            # Combined prediction
            predicted_price = current * seasonal_factor * (1 + random_change) * trend
            predicted_price = max(current_price * 0.7, predicted_price)  # Don't drop too much
            
            predictions.append({
                'date': date.isoformat(),
                'price': round(predicted_price, 2),
                'day': i + 1
            })
            
            current = predicted_price
        
        return predictions
    
    def calculate_best_sell_date(self, price_predictions):
        """
        Analyze predictions to find best sell date
        
        Returns:
            Dict with best date and expected price
        """
        prices = [p['price'] for p in price_predictions]
        max_price = max(prices)
        max_index = prices.index(max_price)
        
        return {
            'best_date': price_predictions[max_index]['date'],
            'expected_price': max_price,
            'days_to_wait': max_index + 1,
            'potential_gain': round((max_price - price_predictions[0]['price']) / price_predictions[0]['price'] * 100, 2)
        }
    
    def get_price_insights(self, price_predictions):
        """
        Generate insights from price predictions
        """
        prices = [p['price'] for p in price_predictions]
        avg_price = sum(prices) / len(prices)
        max_price = max(prices)
        min_price = min(prices)
        
        # Calculate trend
        first_half = sum(prices[:len(prices)//2]) / (len(prices)//2)
        second_half = sum(prices[len(prices)//2:]) / (len(prices) - len(prices)//2)
        trend = "increasing" if second_half > first_half else "decreasing"
        
        # Calculate volatility
        variance = sum((x - avg_price) ** 2 for x in prices) / len(prices)
        volatility = (variance ** 0.5) / avg_price * 100
        
        return {
            'average_price': round(avg_price, 2),
            'max_price': round(max_price, 2),
            'min_price': round(min_price, 2),
            'trend': trend,
            'volatility': round(volatility, 2),
            'recommendation': generate_sell_recommendation(trend, volatility, prices)
        }
    
    def update_accuracy(self, predicted_price, actual_price):
        """
        Calculate prediction accuracy
        """
        error = abs(predicted_price - actual_price) / actual_price * 100
        return round(100 - error, 2)


def generate_sell_recommendation(trend, volatility, prices):
    """
    Generate selling recommendation based on trend analysis
    """
    first_price = prices[0]
    last_price = prices[-1]
    gain = (last_price - first_price) / first_price * 100
    
    if volatility > 20:
        recommendation = "High price volatility detected. Consider selling during price peaks."
    elif trend == "increasing" and gain > 5:
        recommendation = "Prices are expected to increase. You might benefit by waiting."
    elif trend == "decreasing":
        recommendation = "Prices are declining. Consider selling soon to maximize profit."
    elif gain < -5:
        recommendation = "Market shows downward trend. Recommend immediate sale."
    else:
        recommendation = "Market is stable. You can sell at current market price."
    
    return recommendation


# Global model instance
_price_model = None


def get_price_predictor():
    """Get or initialize price prediction model"""
    global _price_model
    if _price_model is None:
        _price_model = PricePredictionModel()
    return _price_model


def predict_crop_prices(current_price, days_ahead=30, volatility=0.05):
    """
    Convenience function to predict crop prices
    """
    predictor = get_price_predictor()
    predictions = predictor.generate_price_trend(current_price, days_ahead, volatility)
    best_date = predictor.calculate_best_sell_date(predictions)
    insights = predictor.get_price_insights(predictions)
    
    return {
        'predictions': predictions,
        'best_sell_date': best_date,
        'insights': insights,
        'is_mock': True
    }
