release: python manage.py migrate
web: gunicorn asgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gthread --timeout 120 --max-requests 1000 --max-requests-jitter 100
