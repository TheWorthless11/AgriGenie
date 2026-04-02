# Weather & Disaster Forecast - Setup Fix Guide

## Issue
Getting error: **"⚠️ Unable to fetch weather data"** when searching for weather by city

## Root Cause
The OpenWeatherMap API key was not properly configured or there was a mismatch in environment variable naming.

## Solution

### Step 1: Verify .env File
Ensure your `.env` file has the correct API key:

```env
OPENWEATHER_API_KEY=your_actual_api_key_here
```

**Current key in your .env:**
- File location: `/c:\Users\Shaila\.vscode\AgriGenie\AgriGenie\.env`
- Variable: `OPENWEATHER_API_KEY`
- Value: `4d4aac4988e96e3d4cc9219a35936049` ✓

### Step 2: Get a Free OpenWeatherMap API Key (If needed)

1. Visit: https://openweathermap.org/api
2. Sign up for a free account
3. Go to API keys section
4. Copy your API key
5. Update `.env` file:
   ```env
   OPENWEATHER_API_KEY=your_new_key_here
   ```

### Step 3: Fixed Code

The fix has already been applied to:
- **File**: `ai_models/weather_service.py`
- **Change**: Updated to use `OPENWEATHER_API_KEY` from environment

```python
# Before (incorrect)
API_KEY = os.getenv('WEATHER_API_KEY', 'demo_key')

# After (corrected)
API_KEY = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
```

### Step 4: Restart Django Application

After updating `.env`, restart the Django development server:

```bash
py manage.py runserver
```

**OR**

Leave it running and manually reload via CTRL+C and restart.

## How Weather Forecast Works

### Frontend Flow
1. User enters city name in search box
2. JavaScript sends geocoding request to OpenWeatherMap Geo API
3. API converts city name to coordinates (lat/lon)
4. Frontend calls backend weather endpoint with coordinates

### Backend Flow
1. Backend receives lat/lon parameters
2. Fetches weather data from OpenWeatherMap Forecast API
3. Processes and formats the response
4. Returns JSON with weather info, alerts, and 5-day forecast

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `api.openweathermap.org/geo/1.0/direct` | City name → Coordinates (Frontend) |
| `api.openweathermap.org/data/2.5/forecast` | Weather data (Backend) |
| `/api/weather/?lat=X&lon=Y` | AgriGenie backend API |

## Troubleshooting

### Still Getting Error?

1. **Check API key validity**:
   ```bash
   curl "https://api.openweathermap.org/data/2.5/weather?q=Dhaka&appid=YOUR_KEY"
   ```

2. **Verify .env is loaded**:
   - Add debug statement in Python
   - Check Django settings: `from django.conf import settings; print(settings.OPENWEATHER_API_KEY)`

3. **Check browser console for errors**:
   - Open DevTools (F12)
   - Check Console tab for JavaScript errors
   - Look for CORS issues or network errors

4. **Verify network request**:
   - Open Network tab in DevTools
   - Try to fetch weather
   - Check request and response details
   - Verify API key is being sent in URL

## Testing Weather Alerts

Once working, test with:
1. Search by city: "Dhaka, Bangladesh"
2. Search by city: "Kishoreganj"
3. Use current location (browser permission required)
4. Check 5-day forecast displays

## Free Tier Limitations

- Up to 1,000 calls/day
- 5-day forecast available
- Current weather data included
- No historical data or advanced features

For production, consider upgrading to a paid plan for higher limits.

## Additional Resources

- OpenWeatherMap API Docs: https://openweathermap.org/api
- Free API Tier: https://openweathermap.org/api/free
- Pricing: https://openweathermap.org/price

---

**Last Updated**: April 2, 2026
**Status**: ✓ Fixed and Ready
