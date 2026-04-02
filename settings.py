import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Path Configuration (Flattened Level 2 Structure)
BASE_DIR = Path(__file__).resolve().parent

# 2. Load Environment Variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 3. Security Settings
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# 4. Application Definition
INSTALLED_APPS = [
    'daphne',  # MUST be first for ASGI support
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required by allauth
    'channels',              # Django Channels for WebSocket support
    
    # Custom Apps
    'users',
    'farmer',
    'buyer',
    'admin_panel',
    'marketplace',
    'chat',                  # Real-time chat application
    
    # Third-Party Apps
    'rest_framework',
    'django_celery_beat',
    'django_celery_results',
    'corsheaders',
    
    # Google OAuth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1
AUTH_USER_MODEL = 'users.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'admin_panel.middleware.AdminIndexRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required by allauth
]

# 5. Routing Configuration (Updated for Level 2)
ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'
ASGI_APPLICATION = 'asgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 6. Database Configuration
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# 7. Password Validation & Internationalization
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 8. Static & Media Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session reliability (required for Daphne / ASGI)
SESSION_SAVE_EVERY_REQUEST = True

# 9. Authentication & AllAuth Routing
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
SOCIALACCOUNT_LOGIN_ON_GET = True

# 10. Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 11. Celery & Redis Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Updated beat schedule paths pointing directly to tasks.py
CELERY_BEAT_SCHEDULE = {
    'monitor-weather-alerts': {
        'task': 'tasks.monitor_weather_for_farmers',
        'schedule': 3600 * 6,  # Every 6 hours
    },
    'send-new-listing-alerts': {
        'task': 'tasks.send_new_listing_alerts',
        'schedule': 3600 * 4,  # Every 4 hours
    },
    'cleanup-out-of-stock-crops': {
        'task': 'tasks.cleanup_out_of_stock_crops',
        'schedule': 3600,  # Every hour
    },
    'cleanup-old-notifications': {
        'task': 'tasks.cleanup_old_notifications',
        'schedule': 3600 * 24,  # Every 24 hours
    },
    'update-farmer-ratings': {
        'task': 'tasks.update_farmer_ratings',
        'schedule': 3600 * 24,  # Every 24 hours
    },
    'generate-daily-report': {
        'task': 'tasks.generate_daily_report',
        'schedule': 3600 * 24,  # Every 24 hours
    },
    'auto-retrain-price-model': {
        'task': 'tasks.auto_retrain_price_model',
        'schedule': 3600 * 24 * 30,  # Every month
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('CACHE_URL'),
    }
}

# 12. Channels / WebSockets Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', '127.0.0.1'), int(os.getenv('REDIS_PORT', 6379)))],
        },
    },
}

# 13. Other APIs & CORS
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY') or os.getenv('WEATHER_API_KEY')
WEATHER_API_KEY = OPENWEATHER_API_KEY
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
]