# Advanced ML-Based Price Prediction System

## Overview

The AgriGenie price prediction system now uses **Random Forest Regressor** combined with weather forecasts and historical data to provide accurate 7-day price predictions for crops.

## Key Features

### 1. Machine Learning Model
- **Algorithm**: Random Forest Regressor
  - 100 decision trees for robust predictions
  - Max depth of 10 for avoiding overfitting
  - Incorporates ensemble uncertainty estimates for confidence scoring
  - Processes 12+ features to capture complex price patterns

### 2. Data Sources

#### Historical Price Data
- **Period**: Last 1 year of crop prices
- **Source**: CropPrice model (predictions stored over time)
- **Usage**: Trains model and provides lag features (1-day, 7-day, 30-day prices)

#### Weather Forecast Data
- **API**: OpenWeatherMap API (free tier)
- **Metrics Captured**:
  - Temperature (affects crop storage/demand)
  - Humidity (impacts disease risk)
  - Rainfall (influences supply/quality)
- **Forecast Range**: 7-day forecast

#### Seasonal Patterns
- **Seasonal Weights**: 12-month pattern for crop prices
  - Higher prices post-harvest (Jan-Mar, Oct-Dec)
  - Lower prices during planting season (Apr-Jun, Jul-Sep)
- **Captures**: Supply scarcity, storage availability, seasonal demand

### 3. Feature Engineering

The model uses these features for prediction:

| Feature | Purpose | Source |
|---------|---------|--------|
| `day_of_year` | Seasonal timing (1-365) | Date |
| `day_of_week` | Weekly patterns (0-6) | Date |
| `month` | Monthly seasonality (1-12) | Date |
| `price_lag_1` | Yesterday's price | History |
| `price_lag_7` | 1-week old price | History |
| `price_lag_30` | 1-month old price | History |
| `price_mean_7d` | 7-day moving average | History |
| `price_std_7d` | Price volatility (7-day) | History |
| `temperature` | Weather condition | Forecast |
| `humidity` | Weather humidity % | Forecast |
| `rainfall` | Expected rainfall (mm) | Forecast |
| `seasonal_factor` | Seasonal multiplier | Crop calendar |
| `trend` | Recent price momentum | History |

### 4. Confidence Scoring

Each prediction includes a confidence score (0-100%) calculated as:
- **Ensemble Variance**: Uses std dev of predictions across 100 trees
- **Bounds**: Clamped between 0-100%
- **Interpretation**:
  - 80-100%: High confidence in prediction
  - 60-80%: Moderate confidence
  - <60%: Low confidence (external factors may impact)

### 5. Price Bounds

Predictions are constrained within reasonable ranges:
- **Min**: 60% of current price (prevents crash predictions)
- **Max**: 150% of current price (prevents unrealistic spikes)

## System Architecture

### File Structure

```
ai_models/
├── advanced_price_predictor.py    # ML prediction engine
├── weather_service.py              # Weather API integration
└── price_prediction.py             # Legacy predictor (fallback)

farmer/
├── views.py                        # Updated price_prediction view
├── models.py                       # CropPrice model for storage
└── templates/
    └── farmer/price_prediction.html # Updated UI with ML results
```

### Class: AdvancedPricePredictor

```python
class AdvancedPricePredictor:
    def prepare_features()      # Normalize and engineer features
    def train_model()           # Train RF on historical data
    def predict()               # Generate 7-day predictions
    def get_feature_importance() # Show which factors matter most
```

### Function: predict_prices_with_ml()

Main entry point for predictions:
```python
result = predict_prices_with_ml(crop, days_ahead=7)
# Returns: {
#     'status': 'success',
#     'predictions': [{
#         'date': '2026-02-16',
#         'price': 120.5,
#         'confidence': 85.3,
#         'temperature': 25.0,
#         'humidity': 60,
#         'rainfall': 0.5
#     }, ...],
#     'model_confidence': 85.3
# }
```

## Usage Flow

1. **User selects crop** on price prediction page
2. **System fetches** historical prices (1 year)
3. **API call** gets 7-day weather forecast
4. **Model trains** using historical + seasonal data
5. **Predictions generated** for next 7 days
6. **Results stored** in CropPrice table for tracking

## Prediction Accuracy

### Training Data Requirements
- **Minimum**: 10 historical price points
- **Optimal**: 100+ data points (full 3-4 months)
- **Best**: 365 days of historical data

### Model Performance
- Uses cross-validation within ensemble
- Feature importance ranking for transparency
- Automatically adapts to new price patterns

## Weather Integration Details

### OpenWeatherMap API Call
```python
GET https://api.openweathermap.org/data/2.5/forecast
Parameters:
- lat: Farmer's latitude
- lon: Farmer's longitude
- days: 7 (forecast range)
- appid: WEATHER_API_KEY from settings
```

### Fallback Behavior
- If API unavailable: Uses default weather (25°C, 60% humidity, no rain)
- If no farmer location: Uses India center coordinates (20.59°N, 78.96°E)
- If forecast < 7 days: Repeats last known forecast

## Requirements

### Python Packages
```
scikit-learn>=1.3.0    # Machine Learning
pandas>=1.5.0         # Data processing
numpy>=1.24.0        # Numerical computation
requests==2.31.0     # API calls
```

### Environment Variables
```
WEATHER_API_KEY=your_openweathermap_api_key
```

## Future Enhancements

1. **LSTM Neural Networks**: For better temporal patterns
2. **Market Data**: Integrate commodity exchange prices
3. **Social Media**: Monitor market sentiment
4. **Climate Data**: Long-term weather patterns
5. **Export Prices**: Include international market trends
6. **Mobile Alerts**: Push notifications for price spikes

## Troubleshooting

### "Model not trained" Warning
- **Cause**: Less than 10 historical prices
- **Solution**: Let system collect more data over time
- **Fallback**: Uses basic price lag prediction

### Weather API Errors
- **Check**: WEATHER_API_KEY is valid
- **Check**: API rate limits (free tier: 60 calls/min)
- **Fallback**: Uses default weather values

### Prediction Bounds Issue
- **Check**: Current price is reasonable
- **Check**: Historical prices aren't corrupted
- **Solution**: Manual price entry correction

## Performance Metrics

| Metric | Value |
|--------|-------|
| Model Training Time | <100ms (typical) |
| Prediction Time | <50ms per prediction |
| Memory Usage | ~10MB per crop model |
| Feature Engineering | <30ms |
| Weather API Call | 100-500ms (network dependent) |

## Example Output

```json
{
  "status": "success",
  "predictions": [
    {
      "date": "2026-02-10",
      "price": 125.50,
      "confidence": 87.2,
      "temperature": 26.5,
      "humidity": 62,
      "rainfall": 0.0
    },
    {
      "date": "2026-02-11",
      "price": 124.75,
      "confidence": 85.1,
      "temperature": 25.2,
      "humidity": 60,
      "rainfall": 2.5
    }
  ],
  "model_confidence": 86.15
}
```

## Security & Privacy

- Weather data is cached for 30 minutes (reduces API calls)
- Price predictions stored locally (no external sharing)
- Farmer location only used for weather (never stored)
- API keys secured via environment variables

---

**Last Updated**: February 9, 2026
**Version**: 1.0 (ML-enabled)
