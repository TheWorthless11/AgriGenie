# AgriGenie - Smart Agricultural Marketplace

A comprehensive Django-based web application for farmers and buyers to connect in an agricultural marketplace with AI-powered features.

## Features

### Farmer Module ✅
- **Registration & Login**: Secure account creation and authentication
- **Crop Management**: Add, edit, and remove crops for sale
- **AI Disease Detection**: Upload crop images for disease analysis using deep learning
- **Price Prediction**: Get AI-powered crop price forecasts with trend analysis
- **Weather Alerts**: Real-time weather data and disaster warnings
- **Messaging**: Direct communication with buyers
- **Notifications**: Real-time alerts for orders, prices, and weather

### Buyer Module ✅
- **Marketplace**: Browse and search available crops
- **Advanced Filtering**: Filter by crop type, location, price range
- **New Listings**: Automatic alerts for new crop listings
- **Order Management**: Track orders and confirm receipt
- **Wishlist**: Save favorite crops for later
- **Reviews & Ratings**: Leave feedback on crops and farmers

### Admin Module ✅
- **User Management**: Approve/reject users, manage profiles
- **Crop Monitoring**: Monitor and manage crop listings
- **AI Monitoring**: Track disease detection and price prediction accuracy
- **System Analytics**: View statistics and generate reports
- **Activity Logging**: Track all system activities

## Technology Stack

- **Backend**: Django 4.2
- **Database**: SQLite (can be switched to PostgreSQL/MySQL)
- **Frontend**: Bootstrap 5, Chart.js
- **AI/ML**: TensorFlow, ResNet50
- **Task Queue**: Celery + Redis
- **Cache**: Redis
- **API Integration**: OpenWeatherMap, Nominatim

## Installation

### Prerequisites
- Python 3.8+
- Redis Server
- pip (Python package manager)

### Setup Steps

1. **Clone the Repository**
   ```bash
   cd AgriGenie
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configurations
   ```

5. **Initialize Database**
   ```bash
   python manage.py migrate
   python manage.py init_ai_monitoring
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect Static Files** (for production)
   ```bash
   python manage.py collectstatic
   ```

## Running the Application

### Development Server
```bash
python manage.py runserver
```
Access at: http://localhost:8000

### Celery Worker (for background tasks)
```bash
celery -A AgriGenie worker -l info
```

### Celery Beat (for scheduled tasks)
```bash
celery -A AgriGenie beat -l info
```

### Redis Server (Windows)
```bash
redis-server
```

## Project Structure

```
AgriGenie/
├── AgriGenie/              # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── users/                  # User authentication & profiles
├── farmer/                 # Farmer-specific features
├── buyer/                  # Buyer-specific features
├── admin_panel/            # Admin features
├── marketplace/            # Marketplace listings
├── ai_models/              # AI/ML modules
│   ├── disease_detection.py
│   ├── price_prediction.py
│   └── weather_service.py
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── media/                  # User uploads
└── manage.py
```

## Key Features Implementation

### AI Disease Detection
- Uses pre-trained ResNet50 neural network
- Analyzes uploaded crop/leaf images
- Detects fungal, bacterial, viral diseases and pest damage
- Provides treatment recommendations
- Confidence scores for detection accuracy

### Price Prediction
- Analyzes historical price data and market trends
- Generates 30-day price forecasts
- Provides best sell date recommendations
- Shows price volatility analysis
- Interactive Chart.js visualizations

### Weather Integration
- Real-time weather data from OpenWeatherMap API
- Automatic disaster alert generation
- Flood, drought, cyclone, frost, and heat wave warnings
- Location-based weather updates

### Automated Tasks
Celery scheduled tasks:
- Check weather alerts every 6 hours
- Generate price predictions daily
- Send price change alerts every 12 hours
- Alert buyers about new listings every 4 hours
- Clean up old notifications daily
- Update farmer ratings daily
- Generate daily system reports

## API Integrations

### OpenWeatherMap
Get your free API key: https://openweathermap.org/api

Add to .env:
```
WEATHER_API_KEY=your_api_key
```

## Usage Guide

### For Farmers
1. Register as Farmer
2. Complete farm profile
3. Add crops for sale
4. Use disease detection: Go to "Disease Detection" → Upload image
5. Check price predictions: Go to "Price Prediction" → Select crop
6. Monitor weather alerts on dashboard
7. Respond to buyer inquiries

### For Buyers
1. Register as Buyer
2. Browse marketplace
3. Search and filter crops
4. Add crops to wishlist
5. Place orders with farmers
6. Track order status
7. Leave reviews and ratings

### For Admins
1. Login to admin panel
2. Approve/reject user registrations
3. Monitor crop listings
4. Track AI model performance
5. Generate system reports
6. Send system-wide alerts
7. View activity logs

## Database Models

### User Management
- CustomUser (extends Django User)
- FarmerProfile
- BuyerProfile
- Notification

### Farmer Features
- Crop
- Order
- CropDisease
- CropPrice
- WeatherAlert
- Message
- FarmerRating

### Marketplace
- CropListing
- Review
- Search
- CategoryFilter
- PriceHistory

### Admin
- UserApproval
- SystemAlert
- SystemReport
- AIDiseaseMonitor
- AIPricePredictor
- ActivityLog

## Troubleshooting

### Redis Connection Error
- Ensure Redis server is running
- Check connection settings in settings.py

### Celery Tasks Not Running
- Start Celery worker: `celery -A AgriGenie worker -l info`
- Start Celery beat: `celery -A AgriGenie beat -l info`

### Weather API Errors
- Verify API key is correct
- Check API rate limits
- Ensure location is properly formatted

### Image Upload Issues
- Check MEDIA_ROOT and MEDIA_URL settings
- Ensure proper file permissions
- Verify file size limits

## Performance Optimization

1. **Caching**: Redis cache for weather data and frequently accessed data
2. **Pagination**: 12-20 items per page in lists
3. **Database Indexing**: Indexes on user, timestamp, and status fields
4. **Image Optimization**: Automatic image resizing and compression
5. **Lazy Loading**: Images load on-demand in marketplace

## Security Features

- CSRF protection
- Password validation
- Secure authentication
- SQL injection prevention
- XSS protection
- Rate limiting (when deployed)

## Deployment

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Update ALLOWED_HOSTS
- [ ] Use environment variables for secrets
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure static/media file serving
- [ ] Set up HTTPS/SSL
- [ ] Configure email backend
- [ ] Set up logging
- [ ] Configure monitoring

### Deployment Platforms
- Heroku
- PythonAnywhere
- AWS EC2
- DigitalOcean

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Email: support@agrigenie.com
- Documentation: https://agrigenie.readthedocs.io

## Roadmap

- [ ] Mobile application (React Native)
- [ ] Advanced analytics dashboard
- [ ] Payment gateway integration
- [ ] Video tutorials for farmers
- [ ] Multi-language support
- [ ] Blockchain for transaction verification
- [ ] IoT sensor integration
- [ ] Crop insurance marketplace

## Credits

- Django community
- TensorFlow/Keras
- OpenWeatherMap API
- Bootstrap framework

---

**AgriGenie** - Empowering farmers with technology 🌾
