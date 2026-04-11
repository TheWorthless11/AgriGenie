FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install ONLY production requirements (NOT full requirements.txt)
COPY requirements-production.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-production.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media

# Collect static files (don't fail if it errors)
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "asgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "--max-requests", "1000"]
