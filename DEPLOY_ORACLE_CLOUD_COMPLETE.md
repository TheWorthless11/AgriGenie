# Deploy AgriGenie to Oracle Cloud - COMPLETE GUIDE

## 🎯 YOUR GOAL: ALL Features Online 24/7

```
✅ Django Web Server
✅ PostgreSQL Database (Always On)
✅ Redis Cache (Always On)
✅ Celery Workers (Background Tasks)
✅ Celery Beat (Scheduled Tasks)
✅ AI/ML Features (Disease Detection, Price Prediction, Weather)
✅ Real-time Chat (WebSocket)
✅ Admin Panel
✅ REST APIs
✅ Google OAuth
✅ Email System
✅ Public URL with HTTPS
✅ 24/7 Availability (No laptop needed!)
```

---

## 📊 ORACLE CLOUD FREE TIER (Your Resources)

```
✅ 2x Compute Instances (1 OCPU, 1GB RAM each) - Always Free
✅ 100GB Autonomous Database (PostgreSQL) - Always Free
✅ 10GB Autonomous Analytics (Optional)
✅ Load Balancer
✅ VCN (Virtual Cloud Network)
✅ 10GB Object Storage
✅ 24/7 Online
✅ Automatic Backups
✅ No Credit Card Charged (Free Tier Safe)
```

**Cost: $0/month (Free tier, your Visa is just for verification)**

---

# 🚀 STEP-BY-STEP DEPLOYMENT

## ✅ STEP 1: CREATE ORACLE CLOUD ACCOUNT

### **1.1: Sign Up**

1. Go to: https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in details:
   - Email: Your email
   - Password: Strong password
   - Country: Your country
4. Click **"Next"**

### **1.2: Add Billing Information**

When prompted:
1. **Billing Address**: Your address
2. **Card Details**: Your Visa card (won't be charged)
3. Click **"Verify My Card"**
4. Oracle will charge $0.01-$1 (temporary hold, then refund)
5. Confirm the verification code sent to your email

### **1.3: Complete Setup**

1. Choose **Region**: Select closest to you (e.g., `ap-mumbai-1`, `us-phoenix-1`)
2. Click **"Continue"**
3. Wait for account activation (5-10 minutes)
4. You'll receive confirmation email

✅ **Oracle Cloud Account Ready!**

---

## ✅ STEP 2: CREATE COMPUTE INSTANCE (VM)

### **2.1: Launch Console**

1. Log in to: https://cloud.oracle.com
2. Click **"Create a VM Instance"** or go to:
   - **Menu** → **Compute** → **Instances**
   - Click **"Create Instance"**

### **2.2: Configure Instance**

**Basic Settings:**
```
Name: AgriGenie-Server
Image: Ubuntu 22.04 (Always Free Eligible)
Shape: Ampere A1 (VM.Standard.A1.Flex)
  - OCPU: 1
  - Memory: 6 GB
  - Always Free Eligible: ✓
```

### **2.3: VCN & Networking**

```
VCN: Create new VCN
Subnet: Default
Public IP: Assign (checked)
SSH Key: Download and save securely
```

**IMPORTANT: Save the SSH key!**
```
Click "Save Private Key"
Location: c:\Users\Shaila\oracle_key.key
```

### **2.4: Create Instance**

Click **"Create"** and wait (2-3 minutes)

Once **State = RUNNING**:

```
Public IP Address: XXX.XXX.XXX.XXX (Copy this!)
Instance OCID: ocid1.instance... (Save)
```

✅ **VM Instance Running!**

---

## ✅ STEP 3: CONNECT TO YOUR VM

### **3.1: SSH into Instance**

**Windows (PowerShell):**
```powershell
# Navigate to key location
cd c:\Users\Shaila

# Fix key permissions
icacls oracle_key.key /inheritance:r /grant:r "%USERNAME%":"(F)"

# Connect
ssh -i oracle_key.key ubuntu@XXX.XXX.XXX.XXX
```

Replace `XXX.XXX.XXX.XXX` with your **Public IP**

**First-time**: Type `yes` when asked to confirm host key

**You should see:**
```
ubuntu@agrigenie-server:~$
```

✅ **Connected!**

---

## ✅ STEP 4: SETUP PostgreSQL DATABASE

### **4.1: Create Autonomous Database**

1. Go to **Menu** → **Databases** → **Autonomous Database**
2. Click **"Create Autonomous Database"**

**Configure:**
```
Display Name: AgriGenie-DB
Database Name: agrigenie
Admin Password: StrongPass123!@#
  - Min 12 chars, 1 uppercase, 1 lowercase, 1 number, 1 special
Workload Type: Transaction Processing (OLTP)
Deployment Type: Shared Infrastructure
Always Free: ✓ Checked
```

3. Click **"Create Autonomous Database"**
4. Wait (5-10 minutes) for **State = AVAILABLE**

### **4.2: Get Connection String**

1. Click on your database name: **AgriGenie-DB**
2. Click **"Database Connection"**
3. Choose **"TLS"** tab
4. Copy the connection string
5. Should look like:
```
(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.region.oraclecloud.com))...)
```

### **4.3: Get Admin User Password**

1. Go to **SQL Developer Web**
2. Username: `admin`
3. Password: `StrongPass123!@#` (what you set)
4. Click **"Sign In"**

**Run SQL to create app user:**
```sql
CREATE USER agrigenie_user IDENTIFIED BY "AgriGenie@Pass123";
GRANT CREATE SESSION TO agrigenie_user;
GRANT CREATE TABLE TO agrigenie_user;
GRANT UNLIMITED TABLESPACE TO agrigenie_user;
COMMIT;
```

✅ **Database Ready!**

---

## ✅ STEP 5: SETUP REDIS (Create 2nd VM for Redis)

### **5.1: Create Redis Instance**

1. Go to **Compute** → **Instances**
2. Click **"Create Instance"** (Same as before)

**Configuration:**
```
Name: AgriGenie-Redis
Image: Ubuntu 22.04
Shape: VM.Standard.A1.Flex (1 OCPU, 1GB RAM)
SSH Key: Use same key as before
```

3. Click **"Create"**
4. Wait for **RUNNING** state
5. Copy **Public IP**: `YYY.YYY.YYY.YYY`

### **5.2: Install Redis**

SSH into Redis instance:
```bash
ssh -i oracle_key.key ubuntu@YYY.YYY.YYY.YYY
```

**Run commands:**
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Redis
sudo apt install redis-server -y

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping
# Should return: PONG
```

✅ **Redis Running!**

---

## ✅ STEP 6: SETUP SECURITY GROUPS (Firewall)

### **6.1: Add Firewall Rules**

For **AgriGenie-Server** instance:

1. Go to **Compute** → **Instances**
2. Click **AgriGenie-Server**
3. Go to **Linked Resources** → **VCN**
4. Click VCN name
5. Go to **Security Lists**
6. Click default security list
7. Click **"Add Ingress Rule"**

**Add Rules:**

| Port | Protocol | CIDR | Purpose |
|------|----------|------|---------|
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 8000 | TCP | 0.0.0.0/0 | Django Dev |
| 5432 | TCP | 10.0.0.0/16 | PostgreSQL (VCN only) |

✅ **Firewall Configured!**

---

## ✅ STEP 7: DEPLOY AGRIGENIE TO SERVER

### **7.1: SSH into Main Instance**

```bash
ssh -i oracle_key.key ubuntu@XXX.XXX.XXX.XXX
```

### **7.2: Install System Dependencies**

```bash
# Update and upgrade
sudo apt update
sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y \
  python3.12 \
  python3.12-venv \
  python3.12-dev \
  python3-pip \
  git \
  build-essential \
  libpq-dev \
  nginx \
  supervisor \
  curl \
  wget

# Verify Python
python3.12 --version
# Should show: Python 3.12.x
```

### **7.3: Clone Your Project**

```bash
# Create app directory
mkdir -p /home/ubuntu/apps
cd /home/ubuntu/apps

# Clone repository
git clone https://github.com/TheWorthless11/AgriGenie.git
cd AgriGenie

# Verify project exists
ls -la manage.py
```

### **7.4: Create Virtual Environment**

```bash
# Create venv
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Check Python in venv
python --version
# Should show: Python 3.12.x
```

### **7.5: Install Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify critical packages
pip list | grep -E "Django|celery|redis|psycopg2|tensorflow"
```

✅ **Dependencies Installed!**

---

## ✅ STEP 8: CONFIGURE ENVIRONMENT

### **8.1: Create .env File**

```bash
# Create .env
cat > /home/ubuntu/apps/AgriGenie/.env << 'EOF'
# ===== DJANGO SETTINGS =====
DEBUG=False
SECRET_KEY=your-secret-key-here-generate-below
ALLOWED_HOSTS=localhost,127.0.0.1,XXX.XXX.XXX.XXX,yourdomain.com

# ===== DATABASE (Oracle Autonomous) =====
DB_ENGINE=django.db.backends.postgresql
DB_NAME=agrigenie
DB_USER=agrigenie_user
DB_PASSWORD=AgriGenie@Pass123
DB_HOST=adb.region.oraclecloud.com
DB_PORT=1522
DATABASE_URL=postgresql://agrigenie_user:AgriGenie@Pass123@adb.region.oraclecloud.com:1522/agrigenie

# ===== REDIS (Your Redis VM) =====
REDIS_URL=redis://YYY.YYY.YYY.YYY:6379/0
REDIS_HOST=YYY.YYY.YYY.YYY
REDIS_PORT=6379

# ===== CELERY =====
CELERY_BROKER_URL=redis://YYY.YYY.YYY.YYY:6379/0
CELERY_RESULT_BACKEND=redis://YYY.YYY.YYY.YYY:6379/1
CELERY_ALWAYS_EAGER=False

# ===== CACHE =====
CACHE_URL=redis://YYY.YYY.YYY.YYY:6379/2

# ===== EMAIL =====
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# ===== GOOGLE OAUTH =====
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret

# ===== WEATHER API =====
OPENWEATHER_API_KEY=your_weather_api_key

# ===== AWS S3 (Optional) =====
USE_S3=False
AWS_ACCESS_KEY_ID=optional
AWS_SECRET_ACCESS_KEY=optional
AWS_STORAGE_BUCKET_NAME=optional

# ===== SECURITY =====
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
EOF
```

**Replace placeholders:**
- `XXX.XXX.XXX.XXX` → Your **Public IP**
- `YYY.YYY.YYY.YYY` → Your **Redis VM Public IP**
- `adb.region.oraclecloud.com` → Your **Database Host**
- `your_email@gmail.com` → Your email

### **8.2: Generate SECRET_KEY**

```bash
cd /home/ubuntu/apps/AgriGenie
source venv/bin/activate

python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and update `.env`:
```
SECRET_KEY=<paste_output_here>
```

✅ **.env Configured!**

---

## ✅ STEP 9: RUN MIGRATIONS

```bash
cd /home/ubuntu/apps/AgriGenie
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts (username, email, password)

# Collect static files
python manage.py collectstatic --noinput

# Test server locally
python manage.py runserver 0.0.0.0:8000 &
sleep 2
curl http://localhost:8000/
# Should return HTML

# Kill test server
pkill -f "runserver"
```

✅ **Database Ready!**

---

## ✅ STEP 10: SETUP GUNICORN (Production Web Server)

### **10.1: Create Gunicorn Service**

```bash
# Create gunicorn service file
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn daemon for AgriGenie
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/apps/AgriGenie
ExecStart=/home/ubuntu/apps/AgriGenie/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    asgi:application

Environment="PATH=/home/ubuntu/apps/AgriGenie/venv/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### **10.2: Enable and Start Gunicorn**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on reboot)
sudo systemctl enable gunicorn

# Start service
sudo systemctl start gunicorn

# Check status
sudo systemctl status gunicorn

# View logs
sudo journalctl -u gunicorn -f
```

✅ **Gunicorn Running!**

---

## ✅ STEP 11: SETUP CELERY WORKER

### **11.1: Create Celery Worker Service**

```bash
# Create celery worker service
sudo tee /etc/systemd/system/celery.service > /dev/null << 'EOF'
[Unit]
Description=Celery Worker for AgriGenie
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/apps/AgriGenie
ExecStart=/home/ubuntu/apps/AgriGenie/venv/bin/celery \
    -A AgriGenie \
    worker \
    -l info \
    --concurrency=4

Environment="PATH=/home/ubuntu/apps/AgriGenie/venv/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### **11.2: Start Celery Worker**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable
sudo systemctl enable celery

# Start
sudo systemctl start celery

# Check status
sudo systemctl status celery
```

✅ **Celery Worker Running!**

---

## ✅ STEP 12: SETUP CELERY BEAT (Scheduler)

### **12.1: Create Celery Beat Service**

```bash
# Create beat service
sudo tee /etc/systemd/system/celery-beat.service > /dev/null << 'EOF'
[Unit]
Description=Celery Beat for AgriGenie
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/apps/AgriGenie
ExecStart=/home/ubuntu/apps/AgriGenie/venv/bin/celery \
    -A AgriGenie \
    beat \
    -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

Environment="PATH=/home/ubuntu/apps/AgriGenie/venv/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### **12.2: Start Celery Beat**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable
sudo systemctl enable celery-beat

# Start
sudo systemctl start celery-beat

# Check status
sudo systemctl status celery-beat
```

✅ **Celery Beat Running!**

---

## ✅ STEP 13: SETUP NGINX (Reverse Proxy)

### **13.1: Create Nginx Config**

```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/agrigenie > /dev/null << 'EOF'
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name XXX.XXX.XXX.XXX;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name XXX.XXX.XXX.XXX;

    # Self-signed SSL (We'll replace with Let's Encrypt later)
    ssl_certificate /etc/ssl/certs/self-signed.crt;
    ssl_certificate_key /etc/ssl/private/self-signed.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Logging
    access_log /var/log/nginx/agrigenie-access.log;
    error_log /var/log/nginx/agrigenie-error.log;

    # Client max body size for uploads
    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /home/ubuntu/apps/AgriGenie/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/ubuntu/apps/AgriGenie/media/;
        expires 7d;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://gunicorn;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API and dynamic content
    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

**Replace `XXX.XXX.XXX.XXX` with your Public IP**

### **13.2: Enable Nginx**

```bash
# Create self-signed SSL (temporary)
sudo mkdir -p /etc/ssl/private
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/self-signed.key \
    -out /etc/ssl/certs/self-signed.crt

# Enable site
sudo ln -s /etc/nginx/sites-available/agrigenie /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

✅ **Nginx Running!**

---

## ✅ STEP 14: SETUP SSL WITH LET'S ENCRYPT

### **14.1: Install Certbot**

```bash
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot certonly --nginx -d yourdomain.com
# (Skip if no domain yet, use IP-based access)
```

### **14.2: Update Nginx with SSL**

If you have a domain, certbot will automatically update nginx config.

✅ **SSL Configured!**

---

## ✅ STEP 15: VERIFY ALL SERVICES

### **15.1: Check All Services Running**

```bash
# Check Gunicorn
sudo systemctl status gunicorn
# Should be: active (running)

# Check Celery
sudo systemctl status celery
# Should be: active (running)

# Check Celery Beat
sudo systemctl status celery-beat
# Should be: active (running)

# Check Nginx
sudo systemctl status nginx
# Should be: active (running)
```

### **15.2: Test Endpoints**

```bash
# Test Django
curl http://localhost:8000/
# Should return HTML

# Test API
curl http://localhost:8000/api/
# Should return JSON

# Test Admin
curl http://localhost:8000/admin/login/
# Should return login page

# Check Celery tasks
source venv/bin/activate
celery -A AgriGenie inspect active
# Should show workers
```

### **15.3: View Live Logs**

```bash
# Django logs
sudo journalctl -u gunicorn -f

# Celery logs
sudo journalctl -u celery -f

# Nginx logs
sudo tail -f /var/log/nginx/agrigenie-access.log
```

✅ **All Services Running!**

---

## 🌐 STEP 16: ACCESS YOUR APP

### **Your Public URL:**

```
HTTP:  http://XXX.XXX.XXX.XXX/
HTTPS: https://XXX.XXX.XXX.XXX/

Admin: https://XXX.XXX.XXX.XXX/admin/
API:   https://XXX.XXX.XXX.XXX/api/
```

Replace `XXX.XXX.XXX.XXX` with your Public IP

### **Test from Phone/Another PC:**

```
1. Go to: http://XXX.XXX.XXX.XXX
2. You should see your AgriGenie homepage
3. Try to login
4. Try creating a user
5. Try uploading an image (disease detection)
6. Try chat (real-time)
```

✅ **Website Live!**

---

## ✅ FEATURES VERIFICATION

| Feature | Test URL | Expected |
|---------|----------|----------|
| **Homepage** | http://XXX.XXX.XXX.XXX | Visible |
| **Admin Panel** | http://XXX.XXX.XXX.XXX/admin | Login page |
| **API Endpoints** | http://XXX.XXX.XXX.XXX/api | JSON response |
| **User Registration** | Sign up | New user created |
| **Login** | Sign in | Session created |
| **Dashboard** | Dashboard page | Loads correctly |
| **Chat (WebSocket)** | Chat page | Messages send in real-time |
| **Disease Detection** | Upload image | ML model runs (Celery) |
| **Price Prediction** | View prices | Shows predictions |
| **Weather** | Weather widget | Shows current weather |
| **Database** | Create record | Saves to PostgreSQL |
| **Background Tasks** | Check Celery | Tasks execute |
| **Email** | Send email | Email queued in Celery |

---

## 🔧 IMPORTANT CONFIGURATIONS

### **17.1: Update Django Settings**

SSH into server and edit settings.py:

```bash
sudo nano /home/ubuntu/apps/AgriGenie/settings.py
```

Make sure these are set:

```python
# At the top
import os
from pathlib import Path

# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Cache for Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('CACHE_URL', 'redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security for production
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
```

Restart Gunicorn:
```bash
sudo systemctl restart gunicorn
```

### **17.2: Setup Scheduled Tasks**

In Django Admin:
1. Go to Admin: `http://XXX.XXX.XXX.XXX/admin`
2. Go to **Django Celery Beat** → **Periodic Tasks**
3. Add scheduled tasks for:
   - Price prediction updates
   - Weather updates
   - Disease model retraining
   - Email digests

### **17.3: Monitor Performance**

```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h

# Check database connections
sudo -u ubuntu psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 📊 YOUR ORACLE CLOUD BILL

```
Compute Instance (VM):     FREE (Always Free Eligible)
PostgreSQL Autonomous DB:  FREE (Always Free Eligible)
Outbound Traffic:          FREE (up to 10GB/month)
Load Balancer:             FREE
VCN & Security:            FREE

Total Monthly Cost: $0.00

Your Visa Card: NOT CHARGED (Account verified only)
```

---

## 🎯 TROUBLESHOOTING

### **Issue: Django won't start**

```bash
# Check logs
sudo journalctl -u gunicorn -n 50

# Manually test
source /home/ubuntu/apps/AgriGenie/venv/bin/activate
cd /home/ubuntu/apps/AgriGenie
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

### **Issue: Celery not processing tasks**

```bash
# Check Redis connection
redis-cli -h YYY.YYY.YYY.YYY ping

# Check Celery workers
celery -A AgriGenie inspect active

# Check logs
sudo journalctl -u celery -n 50
```

### **Issue: Database connection error**

```bash
# Test database connection
python manage.py dbshell

# Check connection string in .env
cat /home/ubuntu/apps/AgriGenie/.env | grep DATABASE_URL
```

### **Issue: Website not accessible**

```bash
# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check firewall rules in Oracle Cloud
# Portal → Networking → Security Lists → Check Ingress Rules

# Check if port is listening
sudo netstat -tlnp | grep LISTEN
```

### **Issue: SSL certificate errors**

```bash
# If using self-signed cert
curl -k https://XXX.XXX.XXX.XXX

# If using Let's Encrypt
sudo certbot renew --dry-run
sudo systemctl restart nginx
```

---

## 🚀 UPDATES & MAINTENANCE

### **Deploy Updates from GitHub**

```bash
cd /home/ubuntu/apps/AgriGenie
source venv/bin/activate

# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celery-beat
```

### **Backup Database**

```bash
# Download backup from Oracle Cloud console
# Databases → Autonomous Database → AgriGenie-DB → Backup

# Or automatic backups are enabled by default (7-day retention)
```

### **Monitor Logs in Real-time**

```bash
# Create a monitoring script
cat > /home/ubuntu/monitor.sh << 'MONITOR'
#!/bin/bash
watch -n 5 'echo "=== SERVICES ==="; \
  systemctl is-active gunicorn celery celery-beat nginx; \
  echo "=== CONNECTIONS ==="; \
  netstat -tn | grep -E ":(8000|6379|5432)" | wc -l'
MONITOR

chmod +x /home/ubuntu/monitor.sh
/home/ubuntu/monitor.sh
```

---

## ✨ YOU NOW HAVE:

```
✅ Full Django Application
✅ PostgreSQL Database (Always On)
✅ Redis Cache (24/7)
✅ Celery Workers (Unlimited background tasks)
✅ Celery Beat (Scheduled tasks)
✅ AI/ML Features (All working)
✅ Real-time Chat (WebSocket)
✅ Admin Panel
✅ Email System
✅ REST APIs
✅ Security (HTTPS, Nginx)
✅ Performance (Gunicorn + Nginx)
✅ High Availability (Oracle Cloud SLA)
✅ Automatic Backups
✅ 24/7 Online (No laptop needed!)
✅ $0/month Cost (Free Tier)
```

---

## 📞 QUICK SUMMARY

```
1. Create Oracle Cloud account with Visa (Free tier)
2. Create Compute Instance (VM)
3. Create PostgreSQL Autonomous Database
4. Create Redis Instance
5. SSH into main VM
6. Clone your GitHub project
7. Create virtual environment
8. Install all dependencies
9. Configure .env file
10. Run migrations
11. Setup Gunicorn (Django server)
12. Setup Celery Worker
13. Setup Celery Beat
14. Setup Nginx (Reverse proxy)
15. Setup SSL
16. Access your website!

Total setup time: ~1-2 hours
Your app will be online FOREVER (24/7) with $0/month cost!
```

---

## 🎉 YOUR PUBLIC URL IS:

```
🌐 http://XXX.XXX.XXX.XXX

Replace XXX.XXX.XXX.XXX with your Compute Instance Public IP

You can visit from:
✅ Your phone
✅ Another computer
✅ From anywhere in the world
✅ 24/7 (as long as Oracle Cloud is up)
```

---

## 📱 TEST FROM PHONE

1. Find your Public IP
2. On phone, open browser
3. Go to: `http://your.public.ip`
4. You should see YOUR AgriGenie app
5. Try login, registration, chat, everything works!

---

**CONGRATULATIONS! Your AgriGenie is LIVE on the internet!** 🚀

**Next: Follow the steps above and you'll have your first online project deployed!**
