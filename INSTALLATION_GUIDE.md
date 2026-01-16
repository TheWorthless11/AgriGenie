# AgriGenie - Complete Installation & Setup Guide

## System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Redis Server
- Git
- 2GB RAM minimum
- 500MB disk space

## Step-by-Step Installation

### Step 1: Install Python and Redis

#### Windows
1. Download Python from https://www.python.org/downloads/
2. Run installer and check "Add Python to PATH"
3. Download Redis from https://github.com/microsoftarchive/redis/releases
4. Or use Windows Subsystem for Linux (WSL)

#### macOS
```bash
brew install python3
brew install redis
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip redis-server
```

### Step 2: Clone and Setup Project

```bash
# Navigate to desired location
cd /path/to/projects

# Clone repository
git clone https://github.com/yourusername/AgriGenie.git
cd AgriGenie

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env  # Linux/macOS
# or use notepad on Windows
```

Update these key settings:
```
DEBUG=True  # Set to False in production
SECRET_KEY=your-secret-key-here
WEATHER_API_KEY=get-from-openweathermap.org
```

### Step 5: Database Setup

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Initialize AI monitoring
python manage.py init_ai_monitoring

# Create superuser (admin)
python manage.py createsuperuser
```

Follow prompts to create admin account:
- Username: admin
- Email: admin@agrigenie.com
- Password: (secure password)

### Step 6: Collect Static Files (Optional for Development)

```bash
python manage.py collectstatic --noinput
```

### Step 7: Verify Installation

```bash
# Check Django installation
python manage.py check

# Expected output:
# System check identified no issues (0 silenced).
```

## Running the Application

### Terminal 1: Django Development Server
```bash
cd /path/to/AgriGenie
source venv/bin/activate  # Activate venv
python manage.py runserver
```
- Access: http://localhost:8000
- Admin: http://localhost:8000/admin

### Terminal 2: Redis Server
```bash
# Windows (if installed via WSL or native)
redis-server

# macOS
redis-server

# Linux
sudo redis-server
```

### Terminal 3: Celery Worker
```bash
cd /path/to/AgriGenie
source venv/bin/activate  # Activate venv
celery -A AgriGenie worker -l info
```

### Terminal 4: Celery Beat (Optional for scheduled tasks)
```bash
cd /path/to/AgriGenie
source venv/bin/activate  # Activate venv
celery -A AgriGenie beat -l info
```

## First Time Setup

### 1. Create Test Users

**Farmer User:**
- Go to: http://localhost:8000/register
- Username: farmer1
- Email: farmer1@test.com
- Password: TestPass123!
- Role: Farmer

**Buyer User:**
- Go to: http://localhost:8000/register
- Username: buyer1
- Email: buyer1@test.com
- Password: TestPass123!
- Role: Buyer

### 2. Admin Approval

- Go to: http://localhost:8000/admin/
- Login with superuser credentials
- Navigate to User Approvals
- Approve farmer and buyer registrations

### 3. Complete Profiles

**For Farmers:**
- Login as farmer1
- Go to Profile
- Fill farm details:
  - Farm Name
  - Farm Size
  - Farm Location
  - Soil Type
  - Experience Years

**For Buyers:**
- Login as buyer1
- Go to Profile
- Fill buyer details:
  - Company Name (optional)
  - Business Type

### 4. Add Sample Crops

- Login as farmer1
- Go to "Add Crop"
- Fill details:
  - Crop Name: Tomato
  - Crop Type: Vegetable
  - Quantity: 100
  - Unit: kg
  - Price: 50
  - Location: [Your Location]
  - Quality Grade: A
  - Upload image

### 5. Test Features

**Disease Detection:**
- Go to "Disease Detection"
- Select crop
- Upload leaf image
- View results

**Price Prediction:**
- Go to "Price Prediction"
- Select crop
- View 30-day forecast chart

**Weather Alerts:**
- Go to "Weather & Disaster Alerts"
- View real-time weather
- Check alerts (if any)

**Marketplace:**
- Login as buyer1
- Go to "Marketplace"
- Search and browse crops
- Add to wishlist
- Place order

## Configuration Details

### Database Settings

Default SQLite (Development):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

For Production PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'agrigenie_db',
        'USER': 'agrigenie_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Email Configuration

Gmail SMTP:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

Get Gmail App Password:
1. Go to myaccount.google.com
2. Enable 2-factor authentication
3. Generate app-specific password
4. Use that password in EMAIL_HOST_PASSWORD

### Weather API Setup

1. Go to https://openweathermap.org/api
2. Sign up for free account
3. Get API key from dashboard
4. Add to .env: `WEATHER_API_KEY=your_key`

## Common Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'django'"
**Solution:**
```bash
# Check if venv is activated
which python  # Should show venv path
# If not, activate venv:
source venv/bin/activate
pip install django
```

### Issue 2: "redis.ConnectionError: Error 111 connecting to localhost:6379"
**Solution:**
```bash
# Start Redis server
redis-server

# Or check if Redis is already running:
redis-cli ping  # Should return PONG
```

### Issue 3: "Port 8000 already in use"
**Solution:**
```bash
# Use different port:
python manage.py runserver 8080

# Or kill process using port 8000:
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000 | kill -9 <PID>
```

### Issue 4: Images not uploading
**Solution:**
```bash
# Ensure media directory exists:
mkdir -p media

# Check MEDIA_ROOT and MEDIA_URL in settings.py
# Verify file permissions
chmod -R 755 media
```

### Issue 5: "Celery not receiving tasks"
**Solution:**
```bash
# Ensure Redis is running
redis-cli ping  # Should return PONG

# Restart Celery worker:
celery -A AgriGenie worker --purge -l info
```

## Performance Tuning

### For Development
```python
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}
```

### For Production
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql'}}
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test farmer
python manage.py test buyer

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Maintenance Tasks

### Regular Backups
```bash
# Backup database
python manage.py dumpdata > backup.json

# Backup media files
tar -czf media_backup.tar.gz media/
```

### Clean Up
```bash
# Remove old notifications
python manage.py cleanup_old_notifications

# Clear cache
python manage.py clear_cache

# Optimize images
python manage.py optimize_images
```

## Deployment Preparation

### Checklist
- [ ] DEBUG = False
- [ ] SECRET_KEY is strong and secret
- [ ] ALLOWED_HOSTS configured
- [ ] Database backup tested
- [ ] Static files collected
- [ ] Media file permissions verified
- [ ] Email credentials configured
- [ ] SSL/HTTPS enabled
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Celery workers configured
- [ ] Redis persistence enabled

### Using Gunicorn (Production)
```bash
pip install gunicorn
gunicorn AgriGenie.wsgi --workers 4 --bind 0.0.0.0:8000
```

### Using Nginx Reverse Proxy
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://django;
    }
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
}
```

## Support & Documentation

- **Issue Tracker**: https://github.com/yourusername/AgriGenie/issues
- **Documentation**: https://agrigenie.readthedocs.io
- **Community Forum**: https://forum.agrigenie.com
- **Email**: support@agrigenie.com

## Next Steps

1. Read PROJECT_GUIDE.md for feature overview
2. Check TEMPLATES_GUIDE.md for template customization
3. Review API documentation
4. Explore admin panel features
5. Configure email notifications
6. Set up monitoring and logging

---

**Happy farming with AgriGenie! 🌾**
