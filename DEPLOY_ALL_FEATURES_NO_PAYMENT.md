# Deploy AgriGenie with ALL Features - ZERO Payment Required

## 🎯 THE ONLY TRUE SOLUTION: Self-Host + Cloudflare Tunnel

### **What You Get:**
- ✅ **ALL features** (Celery, WebSocket, chat, everything)
- ✅ **$0 cost** (absolutely free)
- ✅ **NO payment method needed**
- ✅ **HTTPS with free SSL** (Cloudflare)
- ✅ **Public URL** (accessible from anywhere)
- ✅ **Unlimited resources** (your computer power)

### **The Only Requirement:**
- ⚠️ Your computer stays on 24/7
- ⚠️ Stable internet connection required
- ⚠️ Run as background process

---

## 🏗️ ARCHITECTURE

```
Your Computer (stays on 24/7):
├─ Python 3.12 + Django
├─ PostgreSQL/SQLite Database
├─ Redis Cache
├─ Celery Worker (background tasks)
├─ Celery Beat (scheduled tasks)
└─ Cloudflare Tunnel → Exposes to internet

Public Access:
└─ https://agrigenie-XXXX.trycloudflare.com (from anywhere)
```

---

## 📋 PREREQUISITES

1. **Python 3.12** installed
2. **Git** installed
3. **Docker** (optional but recommended)
4. **Internet connection** (stable)
5. **Computer that can stay on 24/7**

---

## 🚀 STEP 1: SETUP POSTGRESQL LOCALLY

### **Option A: Using Docker (Easiest)**

```bash
# Start PostgreSQL in Docker
docker run -d \
  --name postgres-agrigenie \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agrigenie \
  -p 5432:5432 \
  postgres:14-alpine

# Connect to it
psql postgresql://postgres:postgres@localhost:5432/agrigenie
```

### **Option B: Install Locally**

**Windows:**
```bash
# Using Chocolatey
choco install postgresql

# Or download from: https://www.postgresql.org/download/windows/
```

**Mac:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### **Create Database & User**

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql:
CREATE DATABASE agrigenie;
CREATE USER agrigenie_user WITH PASSWORD 'YourPassword123!';
GRANT ALL PRIVILEGES ON DATABASE agrigenie TO agrigenie_user;
\q
```

---

## 🚀 STEP 2: SETUP REDIS LOCALLY

### **Option A: Using Docker (Easiest)**

```bash
# Start Redis in Docker
docker run -d \
  --name redis-agrigenie \
  -p 6379:6379 \
  redis:7-alpine

# Test connection
redis-cli ping  # Should return: PONG
```

### **Option B: Install Locally**

**Windows:**
```bash
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use: choco install redis-64
choco install redis-64
redis-server

# In another terminal
redis-cli ping
```

**Mac:**
```bash
brew install redis
brew services start redis
redis-cli ping
```

**Linux (Ubuntu):**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
redis-cli ping
```

---

## 🚀 STEP 3: SETUP DJANGO

### **Step 1: Clone Project**

```bash
cd ~/Desktop  # Or any working directory
git clone https://github.com/TheWorthless11/AgriGenie.git
cd AgriGenie
```

### **Step 2: Create Virtual Environment**

```bash
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### **Step 3: Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### **Step 4: Create .env File**

```bash
cat > .env << EOF
# Django
DEBUG=False
SECRET_KEY=django-insecure-GENERATE_NEW_SECRET_KEY_HERE
ALLOWED_HOSTS=localhost,127.0.0.1,*.trycloudflare.com

# Database - PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=agrigenie
DB_USER=agrigenie_user
DB_PASSWORD=YourPassword123!
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://agrigenie_user:YourPassword123!@localhost:5432/agrigenie

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CACHE_URL=redis://localhost:6379/2

# Email (optional - use console for testing)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# APIs (optional)
GOOGLE_CLIENT_ID=your_google_id
GOOGLE_CLIENT_SECRET=your_google_secret
OPENWEATHER_API_KEY=your_weather_api_key
EOF
```

### **Step 5: Generate SECRET_KEY**

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy output and update `.env`:
```
SECRET_KEY=<paste_output_here>
```

### **Step 6: Run Migrations**

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 🚀 STEP 4: START DJANGO SERVER

### **Terminal 1: Django Web Server**

```bash
cd ~/Desktop/AgriGenie
source venv/bin/activate  # Or venv\Scripts\activate on Windows

python manage.py runserver 0.0.0.0:8000
```

**Output should show:**
```
Starting development server at http://0.0.0.0:8000/
```

✅ Django is running on `http://localhost:8000`

---

## 🚀 STEP 5: START CELERY WORKER

### **Terminal 2: Celery Worker**

```bash
cd ~/Desktop/AgriGenie
source venv/bin/activate

celery -A AgriGenie worker -l info
```

**Output should show:**
```
[*] Connected to redis://localhost:6379/0
[*] Ready to accept tasks
```

✅ Celery Worker is running

---

## 🚀 STEP 6: START CELERY BEAT (Scheduler)

### **Terminal 3: Celery Beat**

```bash
cd ~/Desktop/AgriGenie
source venv/bin/activate

celery -A AgriGenie beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Output should show:**
```
[*] celery beat v5.3.1
[*] LocalTime -> XXXX-XX-XX XX:XX:XX
[*] Scheduler: django_celery_beat.schedulers:DatabaseScheduler
[*] Instance is ready
```

✅ Celery Beat is running (scheduled tasks work)

---

## 🌐 STEP 7: INSTALL CLOUDFLARE TUNNEL

### **Terminal 4: Cloudflare Tunnel Setup**

**Windows:**
```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-applications/install-and-setup/tunnel-guide/

# Or use Python:
pip install cloudflare-tunnel

# Or download binary
iwr https://github.com/cloudflare/cloudflared/releases/latest -OutFile cloudflared.exe
```

**Mac:**
```bash
brew install cloudflare/cloudflare/cloudflared
```

**Linux:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

### **Verify Installation**

```bash
cloudflared --version
```

Should output version number.

---

## 🚀 STEP 8: CREATE CLOUDFLARE TUNNEL

### **Terminal 4: Create & Run Tunnel**

```bash
# Authenticate with Cloudflare
cloudflared tunnel login

# Create tunnel (one-time)
cloudflared tunnel create agrigenie

# Start tunnel - expose your local Django to internet
cloudflared tunnel run --url http://localhost:8000 agrigenie
```

**Output will show:**
```
+----------------------------+--------+
| Tunnel                    | UUID   |
+----------------------------+--------+
| agrigenie                 | XXXXX  |
+----------------------------+--------+

Your quick tunnel has been created! 
Visit it at: https://agrigenie-XXXX.trycloudflare.com
```

---

## ✅ YOUR APP IS NOW LIVE!

### **Access Your App From Anywhere:**

```
Main App:     https://agrigenie-XXXX.trycloudflare.com
Admin Panel:  https://agrigenie-XXXX.trycloudflare.com/admin
Local Access: http://localhost:8000
```

Replace `XXXX` with your actual tunnel ID.

---

## 📊 VERIFICATION CHECKLIST

Check that **everything is running**:

```bash
# Terminal 1: Django ✓
# Terminal 2: Celery Worker ✓
# Terminal 3: Celery Beat ✓
# Terminal 4: Cloudflare Tunnel ✓
```

### **Test Each Component:**

**Django:**
```bash
curl http://localhost:8000
# Should return HTML
```

**Redis:**
```bash
redis-cli ping
# Should return: PONG
```

**Celery:**
```bash
celery -A AgriGenie inspect active
# Should show celery status
```

**PostgreSQL:**
```bash
psql -U agrigenie_user -d agrigenie -c "SELECT 1"
# Should return: 1
```

---

## 📝 TERMINAL SETUP (Permanent)

To make this easier, create a script:

**Windows - `start.bat`:**
```batch
@echo off
REM Start PostgreSQL Docker
docker run -d --name postgres-agrigenie -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:14-alpine

REM Start Redis Docker
docker run -d --name redis-agrigenie -p 6379:6379 redis:7-alpine

REM Start Django in new window
start "Django" cmd /k "cd AgriGenie && venv\Scripts\activate && python manage.py runserver 0.0.0.0:8000"

REM Start Celery Worker in new window
start "Celery Worker" cmd /k "cd AgriGenie && venv\Scripts\activate && celery -A AgriGenie worker -l info"

REM Start Celery Beat in new window
start "Celery Beat" cmd /k "cd AgriGenie && venv\Scripts\activate && celery -A AgriGenie beat -l info"

REM Start Tunnel in new window
start "Tunnel" cmd /k "cloudflared tunnel run --url http://localhost:8000 agrigenie"

echo All services started!
```

**Mac/Linux - `start.sh`:**
```bash
#!/bin/bash

# Start PostgreSQL Docker
docker run -d --name postgres-agrigenie -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:14-alpine &

# Start Redis Docker
docker run -d --name redis-agrigenie -p 6379:6379 redis:7-alpine &

# Start Django
(cd AgriGenie && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000) &

# Start Celery Worker
(cd AgriGenie && source venv/bin/activate && celery -A AgriGenie worker -l info) &

# Start Celery Beat
(cd AgriGenie && source venv/bin/activate && celery -A AgriGenie beat -l info) &

# Start Tunnel
cloudflared tunnel run --url http://localhost:8000 agrigenie &

echo "All services started!"
wai
```

---

## 🔧 TROUBLESHOOTING

### **Issue: Connection to PostgreSQL refused**

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Or for local install
psql -U postgres -d postgres -c "SELECT 1"
```

### **Issue: Redis connection error**

```bash
# Check if Redis is running
redis-cli ping

# If not running
redis-server
```

### **Issue: Celery tasks not running**

```bash
# Check Celery connections
celery -A AgriGenie inspect active

# Check Celery worker logs
celery -A AgriGenie worker -l debug
```

### **Issue: Tunnel not connecting**

```bash
# Re-authenticate
cloudflared tunnel login

# Create new tunnel
cloudflared tunnel create agrigenie-new

# Run tunnel
cloudflared tunnel run --url http://localhost:8000 agrigenie-new
```

### **Issue: Static files not loading**

```bash
cd AgriGenie
python manage.py collectstatic --clear --noinput
```

---

## 🎯 FEATURES VERIFICATION

Check that **all features work**:

| Feature | Test |
|---------|------|
| **Django** | Visit https://agrigenie-XXXX.trycloudflare.com |
| **Admin** | Login at https://agrigenie-XXXX.trycloudflare.com/admin |
| **Database** | Create user, it saves |
| **Celery Tasks** | Check task execution in logs |
| **Background Jobs** | Celery Beat runs scheduled tasks |
| **Real-time Chat** | WebSocket works via Channels |
| **Caching** | Redis cache active |
| **Email** | Console email backend for testing |
| **APIs** | REST endpoints work |
| **Authentication** | Google OAuth if configured |

---

## 📊 RESOURCES USED

```
Your Computer (Always Running):
├─ CPU: ~5-10% (Django + Celery + Redis)
├─ RAM: ~1-2GB (PostgreSQL + Redis + Django)
├─ Disk: ~500MB (application + database)
├─ Internet: ~1-10 Mbps (depending on traffic)
└─ Electricity: your computer power bill

Cost: $0.00/month
Payment Method Required: NONE
Features: ALL 100% ✓
```

---

## 🎁 BONUS: KEEP RUNNING 24/7

To keep your computer running all the time:

**Windows:**
1. Disable sleep mode
   - Settings → Power → Screen timeout
   - Set to "Never"
2. Use Task Scheduler to restart script on boot
3. Or use "Always-On" power plan

**Mac:**
1. System Preferences → Energy Saver
2. Uncheck "Put hard disks to sleep"
3. Check "Prevent computer from sleeping"

**Linux:**
```bash
# Disable sleep
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

---

## 🚀 YOU'RE LIVE!

Your AgriGenie app is now running with:

```
✅ Django Web Server
✅ PostgreSQL Database
✅ Redis Cache
✅ Celery Workers (unlimited background tasks)
✅ Celery Beat (scheduled tasks)
✅ Real-time Chat (WebSocket via Channels)
✅ Public HTTPS URL (https://agrigenie-XXXX.trycloudflare.com)
✅ ZERO payment required
✅ ZERO payment method needed
✅ ALL features working
```

---

## 💡 IMPORTANT: Keep Everything Running

To access your app from anywhere:

1. **Keep computer ON 24/7**
2. **Keep terminal windows open**
3. **Keep internet connection stable**
4. **Monitor the processes**

When you want to stop:
```bash
# Press Ctrl+C in each terminal to stop
```

---

## 🎓 WHEN YOU GRADUATE

When you have a payment method:
1. Migrate to Oracle Cloud ($0/month with payment on file)
2. Or migrate to Fly.io ($5/month)
3. Or migrate to Railway ($0-7/month)

For now, **this self-hosted setup is your solution!**

---

## 📞 QUICK START SUMMARY

```
1. Install Docker (PostgreSQL + Redis)
2. Clone project
3. Install requirements
4. Create .env
5. Run migrations
6. Terminal 1: python manage.py runserver 0.0.0.0:8000
7. Terminal 2: celery -A AgriGenie worker -l info
8. Terminal 3: celery -A AgriGenie beat -l info
9. Terminal 4: cloudflared tunnel run --url http://localhost:8000 agrigenie
10. Visit: https://agrigenie-XXXX.trycloudflare.com
11. LOGIN & USE YOUR APP! 🎉
```

**Total time: ~30 minutes to get everything running**

---

## ✨ YOU NOW HAVE:

- ✅ ALL project features
- ✅ $0 cost
- ✅ NO payment method needed
- ✅ Public accessible app
- ✅ HTTPS SSL (free)
- ✅ Background tasks (Celery)
- ✅ Real-time chat (WebSocket)
- ✅ Production-like setup

**This is the ONLY TRUE FREE SOLUTION with ALL features!** 🚀

---

**Start now! Your app will be live today with ZERO payment! 💪**
