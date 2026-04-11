# Oracle Cloud Deployment - Quick Start Checklist

## 📋 BEFORE YOU START

- [ ] Visa card ready
- [ ] Email address
- [ ] Phone for verification code
- [ ] 2-3 hours free time
- [ ] GitHub repository access
- [ ] SSH key generator ready

---

## 🚀 PHASE 1: SETUP (30 minutes)

### Account & Cloud Setup
- [ ] Go to https://www.oracle.com/cloud/free/
- [ ] Click "Start for free"
- [ ] Fill in registration details
- [ ] Add Visa card (will not be charged)
- [ ] Verify card with OTP
- [ ] Choose region (nearest to you)
- [ ] Account activation complete

### **✓ Result**: Oracle Cloud account ready, FREE tier active

---

## 🖥️ PHASE 2: CREATE RESOURCES (45 minutes)

### Compute Instance (Django Server)
- [ ] Go to Compute → Instances
- [ ] Create Instance
  - [ ] Name: `AgriGenie-Server`
  - [ ] Image: Ubuntu 22.04
  - [ ] Shape: Ampere A1 (1 OCPU, 6GB RAM)
  - [ ] SSH Key: Download and Save
- [ ] Click Create and wait for RUNNING
- [ ] Copy Public IP address

### PostgreSQL Database
- [ ] Go to Databases → Autonomous Database
- [ ] Create Autonomous Database
  - [ ] Name: `AgriGenie-DB`
  - [ ] Password: Strong (12+ chars, mixed case, numbers)
  - [ ] Type: Transaction Processing (OLTP)
  - [ ] Always Free: Checked
- [ ] Click Create and wait for AVAILABLE
- [ ] Note down database host
- [ ] Create app user with SQL

### Redis Instance
- [ ] Create another Compute Instance
  - [ ] Name: `AgriGenie-Redis`
  - [ ] Image: Ubuntu 22.04
  - [ ] Shape: Same as Django
  - [ ] SSH Key: Same key
- [ ] Copy Public IP for Redis
- [ ] Install Redis on it:
  ```bash
  sudo apt update && sudo apt install redis-server -y
  sudo systemctl start redis-server
  redis-cli ping  # Should return: PONG
  ```

### Firewall Rules
- [ ] Go to VCN → Security Lists
- [ ] Add Ingress Rules:
  - [ ] Port 80 (HTTP)
  - [ ] Port 443 (HTTPS)
  - [ ] Port 8000 (Django Dev)

### **✓ Result**: All cloud resources created and configured

---

## 🔧 PHASE 3: DEPLOY APPLICATION (90 minutes)

### Connect to Server
- [ ] SSH into Django server using downloaded key
- [ ] Verify connection works

### Install System Dependencies
- [ ] Update system: `sudo apt update && sudo apt upgrade -y`
- [ ] Install: Python 3.12, git, build-essential, postgresql-client, nginx, supervisor
- [ ] Verify: `python3.12 --version`

### Clone and Setup Project
- [ ] Clone repo: `git clone https://github.com/TheWorthless11/AgriGenie.git`
- [ ] Create venv: `python3.12 -m venv venv`
- [ ] Activate: `source venv/bin/activate`
- [ ] Install deps: `pip install -r requirements.txt`
- [ ] Verify: Check TensorFlow, PyTorch installed (for ML)

### Configure Environment
- [ ] Create `.env` file with:
  - [ ] Django settings (SECRET_KEY, DEBUG=False, ALLOWED_HOSTS)
  - [ ] Database credentials (PostgreSQL Autonomous DB)
  - [ ] Redis connection (Redis VM IP)
  - [ ] Celery configuration
  - [ ] Email credentials
  - [ ] API keys (Google OAuth, OpenWeather)
- [ ] Generate SECRET_KEY from Django
- [ ] Test: `python manage.py check`

### Database Setup
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static: `python manage.py collectstatic --noinput`

### **✓ Result**: Application ready to run

---

## 🎯 PHASE 4: START SERVICES (30 minutes)

### Gunicorn (Web Server)
- [ ] Create systemd service file
- [ ] Enable: `sudo systemctl enable gunicorn`
- [ ] Start: `sudo systemctl start gunicorn`
- [ ] Verify: `sudo systemctl status gunicorn`

### Celery Worker
- [ ] Create systemd service file
- [ ] Enable: `sudo systemctl enable celery`
- [ ] Start: `sudo systemctl start celery`
- [ ] Verify: `sudo systemctl status celery`

### Celery Beat
- [ ] Create systemd service file
- [ ] Enable: `sudo systemctl enable celery-beat`
- [ ] Start: `sudo systemctl start celery-beat`
- [ ] Verify: `sudo systemctl status celery-beat`

### Nginx (Reverse Proxy)
- [ ] Create nginx config file
- [ ] Enable site: `sudo ln -s /etc/nginx/sites-available/agrigenie /etc/nginx/sites-enabled/`
- [ ] Create self-signed SSL
- [ ] Restart: `sudo systemctl restart nginx`

### **✓ Result**: All services running 24/7

---

## ✅ PHASE 5: VERIFY & TEST (15 minutes)

### Basic Checks
- [ ] All services running: `sudo systemctl status gunicorn celery celery-beat nginx`
- [ ] Django loads: `curl http://localhost:8000`
- [ ] Redis works: `redis-cli -h REDIS_IP ping`
- [ ] Database connected: `python manage.py dbshell`

### Web Access
- [ ] Visit: `http://YOUR_PUBLIC_IP`
- [ ] Should see your AgriGenie homepage
- [ ] Admin: `http://YOUR_PUBLIC_IP/admin`
- [ ] Login with superuser credentials

### Feature Testing
- [ ] **User Registration**: Create account
- [ ] **Login**: Sign in and access dashboard
- [ ] **Chat**: Send message (WebSocket test)
- [ ] **Disease Detection**: Upload image (ML + Celery test)
- [ ] **Price Prediction**: View prices (AI test)
- [ ] **Weather**: Check weather widget
- [ ] **Database**: Create record, verify in DB
- [ ] **Background Tasks**: Check Celery logs for task execution
- [ ] **Email**: Try sending email (check Celery queue)

### **✓ Result**: All features working perfectly!

---

## 🌍 YOUR LIVE WEBSITE

```
🔗 Main URL:  http://YOUR_PUBLIC_IP
🔐 Secure:    https://YOUR_PUBLIC_IP (with self-signed or Let's Encrypt SSL)
⚙️ Admin:     http://YOUR_PUBLIC_IP/admin
📱 API:       http://YOUR_PUBLIC_IP/api
💬 Chat:      http://YOUR_PUBLIC_IP/chat (WebSocket)
🤖 ML:        http://YOUR_PUBLIC_IP/disease-detection (Upload image)
💱 Prices:    http://YOUR_PUBLIC_IP/prices (Price prediction)
⛅ Weather:   http://YOUR_PUBLIC_IP/weather (OpenWeatherMap API)
```

Replace `YOUR_PUBLIC_IP` with your Compute Instance's Public IP address

---

## 📱 TEST FROM YOUR PHONE

1. Find your Public IP from Oracle Cloud console
2. On phone, open any browser
3. Go to: `http://YOUR_PUBLIC_IP`
4. You should see your AgriGenie website
5. Try all features:
   - Register new account
   - Login
   - Use chat (send message to farmer/buyer)
   - Upload image for disease detection
   - Check prices, weather, etc.

**It works from anywhere in the world!** 🌍

---

## 💾 IMPORTANT: Save These Credentials

```
Oracle Cloud:
  - Account Email: _____________
  - Password: _____________

Compute Instance (Django):
  - Public IP: _____________
  - SSH Key: Saved at c:\Users\Shaila\oracle_key.key

Redis Instance:
  - Public IP: _____________
  - SSH Key: Same as above

PostgreSQL Database:
  - Host: _____________
  - User: agrigenie_user
  - Password: _____________
  - Database: agrigenie

Django Superuser:
  - Username: _____________
  - Email: _____________
  - Password: _____________
```

---

## 🔍 TROUBLESHOOTING QUICK FIXES

### "Cannot connect to website"
```bash
ssh -i oracle_key.key ubuntu@COMPUTE_IP
sudo systemctl status gunicorn  # Should be active
sudo systemctl restart gunicorn
curl http://localhost:8000  # Should return HTML
```

### "Celery not running tasks"
```bash
sudo systemctl status celery
sudo journalctl -u celery -n 50  # View logs
celery -A AgriGenie inspect active
```

### "Database connection error"
```bash
cat /home/ubuntu/apps/AgriGenie/.env | grep DATABASE_URL
python manage.py dbshell  # Test connection
```

### "Chat/WebSocket not working"
```bash
# Verify Daphne/Channels in requirements.txt
grep -E "channels|daphne" requirements.txt
```

---

## 📊 MONITORING COMMANDS

### View Real-time Logs
```bash
# Django
sudo journalctl -u gunicorn -f

# Celery
sudo journalctl -u celery -f

# Nginx
sudo tail -f /var/log/nginx/agrigenie-access.log
```

### Check System Resources
```bash
htop           # CPU, RAM usage
df -h          # Disk space
free -h        # Memory info
netstat -tlnp  # Open ports
```

### Celery Task Status
```bash
source venv/bin/activate
celery -A AgriGenie inspect active      # Running tasks
celery -A AgriGenie inspect registered  # Available tasks
celery -A AgriGenie inspect stats       # Stats
```

---

## 🔄 DEPLOYMENT UPDATES

When you push code updates to GitHub:

```bash
cd /home/ubuntu/apps/AgriGenie
source venv/bin/activate

git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celery-beat
```

---

## 💰 BILLING MONITOR

Check your Oracle Cloud bill every week:

1. Go to: https://cloud.oracle.com
2. Click your profile
3. Go to **Billing and Cost Management** → **Cost Analysis**
4. Should show: **$0.00 charges**

If you see charges:
- [ ] You likely exceeded free tier limits
- [ ] Check what's consuming resources
- [ ] Adjust resource configs if needed

**With this setup: $0.00/month guaranteed** ✅

---

## ✨ WHAT YOU'VE ACCOMPLISHED

✅ Deployed Django application online (24/7)
✅ PostgreSQL database in cloud (automatic backups)
✅ Redis caching and Celery queue
✅ Background task processing (AI/ML)
✅ Real-time chat (WebSocket)
✅ Scheduled tasks (Celery Beat)
✅ Professional deployment (Gunicorn + Nginx)
✅ SSL/HTTPS security
✅ Admin panel access
✅ REST API online
✅ **ZERO cost** (Free tier)
✅ **Accessible from anywhere** (phone, laptop, world)
✅ **Your first production deployment!**

---

## 🎓 NEXT STEPS

1. **Test thoroughly**: Use website from phone/PC for 1 week
2. **Monitor performance**: Watch logs and system resources
3. **Backup regularly**: Download database backups
4. **Update code**: Deploy updates via git pull
5. **Get domain**: Attach custom domain (optional)
6. **Scale up**: If needed, upgrade from Always Free

---

## 📞 NEED HELP?

When you get stuck, check:
1. Service status: `sudo systemctl status SERVICE_NAME`
2. Service logs: `sudo journalctl -u SERVICE_NAME -n 50`
3. Django check: `python manage.py check`
4. Database: `python manage.py dbshell`
5. Celery: `celery -A AgriGenie inspect active`

---

## 🚀 FINAL CHECKLIST

Before launching publicly:

- [ ] All services running 24/7
- [ ] Features tested from phone/PC
- [ ] Database backup verified
- [ ] Email system configured
- [ ] SSL certificate installed
- [ ] Security headers added
- [ ] Admin panel secured
- [ ] API endpoints responding
- [ ] Chat working in real-time
- [ ] ML models running (Celery)
- [ ] Scheduled tasks executing
- [ ] Logging configured
- [ ] Error handling in place
- [ ] Rate limiting set up
- [ ] Access logs being recorded

---

**CONGRATULATIONS!**

Your AgriGenie is now a **REAL, PRODUCTION WEBSITE** running on Oracle Cloud! 🎉

It will be **online 24/7** and accessible from **anywhere in the world**! 🌍

**Start with Phase 1 and follow each step - you'll have it live in 2-3 hours!** 💪
