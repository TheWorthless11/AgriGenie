# Railway Deployment - Environment Variables Setup Guide

## 📋 All Required Environment Variables

### **SECTION 1: CRITICAL (Must Add)**

| Variable | Value | Notes |
|----------|-------|-------|
| `SECRET_KEY` | Generate new key | 🔑 **See Step 1 below** |
| `DEBUG` | `False` | ⚠️ Must be False for production |
| `ALLOWED_HOSTS` | `*.railway.app,yourdomain.com` | Replace with your Railway URL |

### **SECTION 2: DATABASE (Auto-Set by Railway)**

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Auto-generated | ✅ Railway creates this when you add PostgreSQL |

**You DON'T need to manually set these:**
- ~~DB_ENGINE~~
- ~~DB_NAME~~
- ~~DB_USER~~
- ~~DB_PASSWORD~~
- ~~DB_HOST~~
- ~~DB_PORT~~

### **SECTION 3: EMAIL (Optional - Only if you want email sending)**

| Variable | Example | Where to Get |
|----------|---------|--------------|
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Use this value as-is |
| `EMAIL_HOST` | `smtp.gmail.com` | Gmail SMTP server |
| `EMAIL_PORT` | `587` | Use this value as-is |
| `EMAIL_USE_TLS` | `True` | Use this value as-is |
| `EMAIL_HOST_USER` | `your_email@gmail.com` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | `16-char app password` | 🔑 **See Step 2 below** |

### **SECTION 4: API KEYS (Optional - Only if you want features)**

| Variable | Value | Where to Get |
|----------|-------|--------------|
| `OPENWEATHER_API_KEY` | Your API key | https://openweathermap.org/api |
| `GOOGLE_CLIENT_ID` | Your client ID | https://console.cloud.google.com |
| `GOOGLE_CLIENT_SECRET` | Your client secret | https://console.cloud.google.com |

### **SECTION 5: REDIS/CELERY (Skip - Not needed for free tier)**

Railway free tier doesn't support Redis. These are **optional**:
- ~~REDIS_HOST~~
- ~~REDIS_PORT~~
- ~~CELERY_BROKER_URL~~
- ~~CELERY_RESULT_BACKEND~~
- ~~CACHE_URL~~

---

## 🔑 How to Generate SECRET_KEY

Run this command in your local terminal:

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Output example:**
```
django-insecure-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

Copy this entire string (it's very long) and paste it in Railway as `SECRET_KEY`.

---

## 🔐 How to Generate Gmail App Password

### **Step 1: Enable 2-Factor Authentication on Gmail**
1. Go to: https://myaccount.google.com/security
2. Click **2-Step Verification**
3. Follow the steps to enable it

### **Step 2: Generate App Password**
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** and **Windows Computer** (or your device)
3. Google will generate a **16-character password**
4. Copy it and use as `EMAIL_HOST_PASSWORD`

---

## 📝 STEP-BY-STEP RAILWAY DEPLOYMENT GUIDE

### **STEP 1: Create Railway Account**
1. Go to https://railway.app
2. Click **Login** → **GitHub**
3. Authorize Railway with your GitHub account

---

### **STEP 2: Create New Project**
1. Click **New Project** → **Deploy from GitHub repo**
2. Search for `AgriGenie`
3. Click to select your repository
4. Click **Deploy**

---

### **STEP 3: Add PostgreSQL Database**
1. Inside your project, click **+ Add Services**
2. Click **Database** → **PostgreSQL**
3. Railway automatically creates `DATABASE_URL` variable
4. **Wait 1-2 minutes for database to initialize**

---

### **STEP 4: Add Environment Variables**

#### **4.1 Go to Variables Section**
1. Click on your **web service** (the main app)
2. Click **Variables** tab

#### **4.2 Add Critical Variables**

**Add these 3:**
```
SECRET_KEY = <paste your generated key from Step above>
DEBUG = False
ALLOWED_HOSTS = *.railway.app
```

#### **4.3 Add Email Variables (Optional)**

**If you want email notifications, add:**
```
EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = your_email@gmail.com
EMAIL_HOST_PASSWORD = <your 16-char Gmail app password>
```

#### **4.4 Add API Keys (Optional)**

**If you want weather & Google OAuth, add:**
```
OPENWEATHER_API_KEY = <get from https://openweathermap.org/api>
GOOGLE_CLIENT_ID = <get from Google Cloud Console>
GOOGLE_CLIENT_SECRET = <get from Google Cloud Console>
```

---

### **STEP 5: Deploy**
1. Click **Deploy** button
2. Railway will:
   - ✅ Install Python packages from `requirements.txt`
   - ✅ Run migrations automatically (from `Procfile`)
   - ✅ Start your Django app with gunicorn
3. **Wait 3-5 minutes**

---

### **STEP 6: Check Logs**
1. Click **Deployments** tab
2. See:
   - ✅ Build progress
   - ✅ Migrations running
   - ✅ App starting

**Look for this message:**
```
Listening on 0.0.0.0:8000
```

---

### **STEP 7: Get Your App URL**
1. In Railway dashboard, look for your **web service**
2. You'll see: `https://agrigenie-production.railway.app` (or similar)
3. **This is your live app URL!**

---

### **STEP 8: Create Superuser Account**

Run this command to create admin account:

```bash
railway run python manage.py createsuperuser
```

Follow the prompts:
```
Username: admin
Email: your@email.com
Password: your_strong_password
```

---

### **STEP 9: Access Your App**

**Visit these URLs:**

| URL | Purpose |
|-----|---------|
| `https://your-app-url` | Main app |
| `https://your-app-url/admin` | Admin panel |
| `https://your-app-url/api` | API endpoints |

---

## ✅ Complete Environment Variables Checklist

Copy-paste template (fill in the blanks):

```
# CRITICAL - Must set
SECRET_KEY=django-insecure-PUT_YOUR_KEY_HERE
DEBUG=False
ALLOWED_HOSTS=*.railway.app

# DATABASE - Auto-set by Railway (don't set manually)
# DATABASE_URL=<auto set when you add PostgreSQL>

# EMAIL - Optional, only if you want email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_16_char_app_password

# APIs - Optional
OPENWEATHER_API_KEY=your_weather_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

---

## 🆘 Troubleshooting

### **Issue: Deployment fails with "No DATABASE_URL"**
**Fix:** 
- Make sure you added PostgreSQL database FIRST
- Wait 2 minutes for it to initialize
- Refresh the page

### **Issue: Migrations didn't run**
**Fix:**
- Check logs in Deployments tab
- Database might still be initializing
- Click **Retry Deploy**

### **Issue: Static files not loading (404 on CSS/images)**
**Fix:**
- Already configured in your settings.py with WhiteNoise
- Clear browser cache (Ctrl+Shift+Delete)

### **Issue: Email not sending**
**Fix:**
- Check `EMAIL_HOST_PASSWORD` is correct (16 chars)
- Make sure 2FA is enabled on Gmail account
- Verify `EMAIL_HOST_USER` is correct

### **Issue: App keeps crashing**
**Fix:**
- Check logs for error messages
- Look for "SECRET_KEY not set" errors
- Check database connection errors

---

## 🎯 Quick Copy-Paste Variables

Use this exact format when adding to Railway:

**Variable Name** (left) | **Value** (right)
```
SECRET_KEY | django-insecure-your-key-here
DEBUG | False
ALLOWED_HOSTS | *.railway.app
EMAIL_BACKEND | django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST | smtp.gmail.com
EMAIL_PORT | 587
EMAIL_USE_TLS | True
EMAIL_HOST_USER | your_email@gmail.com
EMAIL_HOST_PASSWORD | your_16_char_password
OPENWEATHER_API_KEY | your_key
GOOGLE_CLIENT_ID | your_id
GOOGLE_CLIENT_SECRET | your_secret
```

---

## 📞 Need More Help?

- **Railway Docs:** https://docs.railway.app
- **Django Docs:** https://docs.djangoproject.com
- **Our Deployment Guide:** See RAILWAY_DEPLOYMENT_GUIDE.md

---

**Ready? Start at Step 1 above! 🚀**
