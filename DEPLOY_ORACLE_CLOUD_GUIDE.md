# Deploy AgriGenie on Oracle Cloud Always-Free Tier

## ✅ Why Oracle Cloud?

- **ABSOLUTELY FREE FOREVER** (no credit card required if qualifying)
- **24GB RAM** (vs Railway's 512MB)
- **4 vCPU** across multiple instances
- **Full Celery support** (unlimited workers)
- **PostgreSQL database** (free)
- **Production-ready infrastructure**

---

## 📋 ORACLE CLOUD FREE TIER RESOURCES

```
Always-Free Tier (Forever):
├─ 1x Compute E2.1.Micro (1 vCPU, 1GB RAM) - ARM64
├─ 2x Compute E2.1.Small (1 vCPU, 2GB RAM each) - ARM64
├─ 2x VM.Standard.E2.1.Micro (1 vCPU, 1GB RAM each) - AMD64
├─ Total: 4 vCPU, 24GB RAM
├─ 20GB Database storage
├─ 160GB monthly data transfer
└─ No expiration, no credit card required*
```

---

## 🚀 DEPLOYMENT ARCHITECTURE

```
Oracle Cloud Setup:

VM1 (Micro, 1GB)     → Django Web Server (Gunicorn)
VM2 (Small, 2GB)     → Celery Worker 1 + Redis Cache
VM3 (Small, 2GB)     → Celery Worker 2 + Celery Beat
VM4 (Micro, 1GB)     → Nginx Reverse Proxy + SSL
└─ Shared: PostgreSQL Database (managed)
```

---

## 📝 STEP 1: CREATE ORACLE CLOUD ACCOUNT

### **1.1 Sign Up**
1. Go to: https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill registration:
   - Email address
   - Country
   - Create password
4. Email verification
5. **NO credit card required** (free tier option available)

### **1.2 Verify & Complete Setup**
1. Check email for verification link
2. Click verification link
3. Complete your profile
4. Select **"Always-Free Tier"** (not trial)
5. Region: Choose closest to you (recommended: **Singapore, Tokyo, or Mumbai** for Asia)

### **1.3 Dashboard**
- Login to: https://console.oracle.com/
- Go to **Compute** → **Instances**

---

## 🖥️ STEP 2: CREATE VIRTUAL MACHINES

### **2.1 Create VM1: Django Web Server**

1. **Go to:** Compute → Instances
2. **Click:** "Create Instance"
3. **Configure:**
   ```
   Name: agrigenie-web
   Image: Ubuntu 22.04 (ARM64)
   Shape: Ampere - VM.Standard.A1.Flex
   OCPU: 1
   RAM: 1GB
   
   Networking: (Use default)
   ```
4. **Add SSH Key:**
   - Click "Save Public Key"
   - Download `ssh-key-XXXX.key`
   - **Save this file safely!**
5. **Click Create Instance**
6. **Wait 2 minutes for it to start**
7. **Copy Public IP** (e.g., `123.45.67.89`)

### **2.2 Create VM2: Celery Worker 1 + Redis**

Repeat process:
```
Name: agrigenie-celery-1
Image: Ubuntu 22.04 (ARM64)
Shape: Ampere - VM.Standard.A1.Flex
OCPU: 1
RAM: 2GB (select this option)
```

### **2.3 Create VM3: Celery Worker 2 + Beat**

Repeat process:
```
Name: agrigenie-celery-2
Image: Ubuntu 22.04 (ARM64)
Shape: Ampere - VM.Standard.A1.Flex
OCPU: 1
RAM: 2GB
```

### **2.4 Create VM4: Nginx Reverse Proxy**

Repeat process:
```
Name: agrigenie-nginx
Image: Ubuntu 22.04 (ARM64)
Shape: Ampere - VM.Standard.A1.Flex
OCPU: 1
RAM: 1GB
```

### **2.5 Configure Firewall Rules**

1. Go to **Networking** → **Virtual Cloud Networks**
2. Click your VCN (Default)
3. Click **Security Lists** → **Default Security List**
4. **Add Ingress Rules:**
   ```
   Protocol: TCP
   Port: 22 (SSH)
   Source: 0.0.0.0/0 (anywhere)
   
   Protocol: TCP
   Port: 80 (HTTP)
   Source: 0.0.0.0/0
   
   Protocol: TCP
   Port: 443 (HTTPS)
   Source: 0.0.0.0/0
   ```
5. **Save**

---

## 🔑 STEP 3: SETUP SSH ACCESS

### **3.1 On Your Local Machine**

```bash
# Set permissions
chmod 400 ssh-key-XXXX.key

# Test SSH access
ssh -i ssh-key-XXXX.key ubuntu@YOUR_VM_PUBLIC_IP

# Example:
ssh -i ssh-key-XXXX.key ubuntu@123.45.67.89
```

### **3.2 You should see:**
```
Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-1018-oracle aarch64)

ubuntu@agrigenie-web:~$
```

---

## 🗄️ STEP 4: SETUP POSTGRESQL DATABASE

### **4.1 Create Database (Via OCI Console)**

1. Go to **Database** → **DB Systems**
2. Click **"Create DB System"**
3. **Configure:**
   ```
   Display Name: agrigenie-db
   DB Engine: PostgreSQL
   DB Version: 14
   Database Name: agrigenie
   Username: postgres
   Password: YourStrongPassword123!
   ```
4. **Click Create** (wait 5-10 minutes)
5. **Get Connection String** from DB System details

### **4.2 Alternative: Simple PostgreSQL on VM**

If OCI Database is complex, install on one VM:

```bash
# SSH into VM2
ssh -i ssh-key-XXXX.key ubuntu@CELERY_VM_IP

# Install PostgreSQL
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE agrigenie;
CREATE USER agrigenie_user WITH PASSWORD 'YourPassword123!';
ALTER ROLE agrigenie_user SET client_encoding TO 'utf8';
ALTER ROLE agrigenie_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE agrigenie_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE agrigenie TO agrigenie_user;
\q
```

---

## 📦 STEP 5: DEPLOY DJANGO ON VM1

### **5.1 SSH into Web VM**

```bash
ssh -i ssh-key-XXXX.key ubuntu@WEB_VM_IP
```

### **5.2 Install Dependencies**

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    nginx \
    curl \
    wget \
    build-essential \
    libpq-dev

# Install Docker (optional but recommended)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

### **5.3 Clone Your Project**

```bash
cd /home/ubuntu
git clone https://github.com/TheWorthless11/AgriGenie.git
cd AgriGenie

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-production.txt
```

### **5.4 Configure Environment Variables**

```bash
# Create .env file
cat > .env << EOF
DEBUG=False
SECRET_KEY=django-insecure-GENERATE_A_NEW_KEY_HERE
ALLOWED_HOSTS=YOUR_DOMAIN_OR_IP,*.oraclecloud.com
DATABASE_URL=postgresql://agrigenie_user:YourPassword123!@DB_VM_IP:5432/agrigenie
REDIS_URL=redis://REDIS_VM_IP:6379/0
CELERY_BROKER_URL=redis://REDIS_VM_IP:6379/0
CELERY_RESULT_BACKEND=redis://REDIS_VM_IP:6379/1
CACHE_URL=redis://REDIS_VM_IP:6379/2
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
GOOGLE_CLIENT_ID=your_google_id
GOOGLE_CLIENT_SECRET=your_google_secret
OPENWEATHER_API_KEY=your_weather_key
EOF
```

### **5.5 Run Migrations**

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### **5.6 Start Django with Gunicorn**

```bash
# Create systemd service
sudo tee /etc/systemd/system/agrigenie.service > /dev/null << EOF
[Unit]
Description=AgriGenie Django Application
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/AgriGenie
Environment="PATH=/home/ubuntu/AgriGenie/venv/bin"
EnvironmentFile=/home/ubuntu/AgriGenie/.env
ExecStart=/home/ubuntu/AgriGenie/venv/bin/gunicorn \
    --workers 2 \
    --worker-class gthread \
    --threads 2 \
    --max-requests 1000 \
    --timeout 120 \
    --bind 0.0.0.0:8000 \
    asgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable agrigenie
sudo systemctl start agrigenie

# Check status
sudo systemctl status agrigenie
```

---

## 🔄 STEP 6: SETUP REDIS ON VM2

### **6.1 SSH into Celery VM1**

```bash
ssh -i ssh-key-XXXX.key ubuntu@CELERY_VM1_IP
```

### **6.2 Install Redis**

```bash
sudo apt-get update
sudo apt-get install -y redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping  # Should return: PONG
```

---

## 🚀 STEP 7: SETUP CELERY WORKER ON VM2

### **7.1 Clone Project & Setup Venv**

```bash
cd /home/ubuntu
git clone https://github.com/TheWorthless11/AgriGenie.git
cd AgriGenie

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements-production.txt
```

### **7.2 Copy .env from Web VM**

```bash
# Get .env from VM1
scp -i ~/ssh-key-XXXX.key ubuntu@WEB_VM_IP:/home/ubuntu/AgriGenie/.env .
```

### **7.3 Create Celery Service**

```bash
# Celery Worker service
sudo tee /etc/systemd/system/celery-worker.service > /dev/null << EOF
[Unit]
Description=AgriGenie Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=ubuntu
WorkingDirectory=/home/ubuntu/AgriGenie
Environment="PATH=/home/ubuntu/AgriGenie/venv/bin"
EnvironmentFile=/home/ubuntu/AgriGenie/.env
ExecStart=/home/ubuntu/AgriGenie/venv/bin/celery -A AgriGenie worker \
    -l info \
    --concurrency=2 \
    --pool=prefork

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
```

---

## ⏰ STEP 8: SETUP CELERY BEAT ON VM3

### **8.1 SSH into VM3**

```bash
ssh -i ssh-key-XXXX.key ubuntu@CELERY_VM2_IP
```

### **8.2 Setup Same as VM2**

```bash
cd /home/ubuntu
git clone https://github.com/TheWorthless11/AgriGenie.git
cd AgriGenie

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements-production.txt

# Copy .env from Web VM
scp -i ~/ssh-key-XXXX.key ubuntu@WEB_VM_IP:/home/ubuntu/AgriGenie/.env .
```

### **8.3 Create Celery Beat Service**

```bash
sudo tee /etc/systemd/system/celery-beat.service > /dev/null << EOF
[Unit]
Description=AgriGenie Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AgriGenie
Environment="PATH=/home/ubuntu/AgriGenie/venv/bin"
EnvironmentFile=/home/ubuntu/AgriGenie/.env
ExecStart=/home/ubuntu/AgriGenie/venv/bin/celery -A AgriGenie beat \
    -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable celery-beat
sudo systemctl start celery-beat
```

---

## 🌐 STEP 9: SETUP NGINX ON VM4

### **9.1 SSH into Nginx VM**

```bash
ssh -i ssh-key-XXXX.key ubuntu@NGINX_VM_IP
```

### **9.2 Install Nginx**

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### **9.3 Configure Nginx**

```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/agrigenie > /dev/null << 'EOF'
upstream django {
    server WEB_VM_IP:8000;
}

server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;
    client_max_body_size 75M;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /home/ubuntu/AgriGenie/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/AgriGenie/media/;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/agrigenie /etc/nginx/sites-enabled/

# Remove default
sudo rm /etc/nginx/sites-enabled/default

# Test nginx
sudo nginx -t

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### **9.4 Setup SSL (HTTPS)**

```bash
# Install SSL certificate (requires domain)
sudo certbot --nginx -d your-domain.com

# Auto-renew
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## ✅ STEP 10: VERIFY DEPLOYMENT

### **10.1 Check Services**

```bash
# On Web VM
sudo systemctl status agrigenie

# On Celery VM1
sudo systemctl status celery-worker
sudo systemctl status redis-server

# On Celery VM2
sudo systemctl status celery-beat

# On Nginx VM
sudo systemctl status nginx
```

### **10.2 View Logs**

```bash
# Django logs
journalctl -u agrigenie -f

# Celery worker logs
journalctl -u celery-worker -f

# Celery beat logs
journalctl -u celery-beat -f
```

### **10.3 Access Your App**

```
Django App: http://YOUR_NGINX_VM_IP
Admin Panel: http://YOUR_NGINX_VM_IP/admin
With SSL: https://your-domain.com
```

---

## 🔧 TROUBLESHOOTING

### **Issue: Connection refused when connecting to DB**

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Allow postgres user login
sudo -u postgres psql
```

### **Issue: Redis connection error**

```bash
# Test Redis connection
redis-cli ping

# Check Redis service
sudo systemctl status redis-server
```

### **Issue: Celery tasks not running**

```bash
# Check Celery worker logs
journalctl -u celery-worker -f

# Verify Redis is accessible from Celery VM
redis-cli -h REDIS_VM_IP ping
```

### **Issue: Static files not loading**

```bash
# Collect static files again
cd /home/ubuntu/AgriGenie
source venv/bin/activate
python manage.py collectstatic --clear --noinput
```

---

## 📊 MONITORING & MAINTENANCE

### **Check VM Health**

```bash
# CPU, Memory, Disk
htop
df -h
free -h

# Network bandwidth
nethogs
```

### **Backup Database**

```bash
# Local backup
pg_dump agrigenie > agrigenie_backup.sql

# Upload to Object Storage
```

### **Update Code**

```bash
cd /home/ubuntu/AgriGenie
git pull origin main
source venv/bin/activate
pip install -r requirements-production.txt
python manage.py migrate
sudo systemctl restart agrigenie
```

---

## 🎯 COST SUMMARY

| Component | Cost |
|-----------|------|
| 4 VMs (Always-Free) | $0 |
| PostgreSQL Database | $0 |
| Redis (self-hosted) | $0 |
| Object Storage | First 20GB free |
| **Total** | **$0/month** |

---

## 🚀 YOU'RE LIVE!

Your AgriGenie app is now running on Oracle Cloud's always-free tier:

```
✅ Django Web Server: Running on VM1
✅ Celery Workers: Running on VM2 & VM3
✅ Redis Cache: Running on VM2
✅ PostgreSQL Database: All data preserved
✅ Nginx Reverse Proxy: Running on VM4
✅ SSL/HTTPS: Configured
✅ Cost: $0/month FOREVER
```

---

## 📞 NEED HELP?

### **Common Commands**

```bash
# Restart everything
sudo systemctl restart agrigenie celery-worker celery-beat

# View realtime logs
journalctl -u agrigenie -f
journalctl -u celery-worker -f

# SSH into Web VM (from your local machine)
ssh -i ssh-key-XXXX.key ubuntu@WEB_VM_IP

# Check current IP of your app
curl http://localhost:8000/health/
```

### **Scale Later**

When you need more power:
- Add more Celery workers (just provision new VMs)
- Increase PostgreSQL resources (paid plan)
- Add load balancing (Nginx on multiple VMs)

---

**Your AgriGenie app is now deployed on Oracle Cloud FREE TIER! 🎉**

Now go to: `http://YOUR_NGINX_VM_IP/admin` and login!
