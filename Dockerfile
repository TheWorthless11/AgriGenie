FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Minimal system dependencies (faster build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media

# Collect static files (don't fail if it errors)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Use gunicorn (lighter than daphne, better for Railway free tier)
CMD ["gunicorn", "asgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
