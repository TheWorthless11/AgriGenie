# Railway.app Deployment Guide for AgriGenie Django

## ✅ Project Files Ready
Your project now has these deployment files:
- `Procfile` - Railway startup configuration
- `runtime.txt` - Python 3.12
- `requirements.txt` - All dependencies (gunicorn, psycopg2, dj-database-url, whitenoise)
- `settings.py` - Updated for production (Railway DATABASE_URL support)

## 📋 Step-by-Step Deployment

### Step 1: Create Railway Account & Link GitHub
1. Go to **https://railway.app**
2. Click **Login** → Choose **GitHub**
3. Authorize Railway
4. Click **New Project** → **Deploy from GitHub repo**

### Step 2: Select Your Repository
1. Search for `AgriGenie`
2. Click to select it
3. Railway will auto-detect it's a Django app

### Step 3: Configure Environment Variables
Railway will prompt you to add environment variables. Add these:

```
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=*.railway.app,yourdomain.com
DB_ENGINE=django.db.backends.postgresql
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

**How to generate SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 4: Create PostgreSQL Database
1. In Railway Dashboard → Click **+ Add**
2. Select **Database** → **PostgreSQL**
3. Railway automatically sets `DATABASE_URL` environment variable

### Step 5: Deploy
1. Click **Deploy** button
2. Railway will:
   - Install requirements.txt
   - Run migrations (from Procfile `release` command)
   - Start the web service

### Step 6: Verify Deployment
1. Check **Deployments** tab for logs
2. Your app URL: `https://agrigenie-production.railway.app` (or similar)

## 🎬 YouTube Videos for Reference

**Django + Railway Deployment (Recommended):**
- Search: **"Deploy Django to Railway.app"**
- Video by **Beau Carnes (freeCodeCamp)**: https://youtube.com/results?search_query=railway+django+deployment

**Quick Setup (5 mins):**
- **Railway Docs**: https://docs.railway.app/guides/django

**Troubleshooting Railway Deployments:**
- **Railway Community**: https://discord.gg/railway

## ❓ Common Issues & Fixes

### Issue: Static files not loading (404)
**Fix:** Already included in your settings:
- WhiteNoise middleware configured
- STATIC_ROOT = `staticfiles/`
- Run: `python manage.py collectstatic --noinput`

### Issue: Database migrations failing
**Fix:** Clear logs and retry:
1. In Railway Dashboard → **View Logs**
2. Click **Retry Deploy**

### Issue: Secret Key not set
**Fix:** Generate and add to Railway:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Issue: Redis/Celery not working
**Fix:** Railway free tier doesn't include Redis
- In-memory cache configured as fallback
- Celery tasks handled gracefully

## 🚀 After Deployment

1. **Create superuser:**
   ```bash
   railway run python manage.py createsuperuser
   ```

2. **Access Admin Panel:**
   - Go to: `https://your-app-url/admin`

3. **Your Django app is live!**

## 📝 Environment Variables Reference

| Variable | Example | Required |
|----------|---------|----------|
| `SECRET_KEY` | `abc123...xyz` | ✅ Yes |
| `DEBUG` | `False` | ✅ Yes |
| `ALLOWED_HOSTS` | `*.railway.app` | ✅ Yes |
| `DATABASE_URL` | Auto-set by PostgreSQL | ✅ Auto |
| `EMAIL_HOST_USER` | `your@gmail.com` | ⚠️ For emails |
| `GOOGLE_CLIENT_ID` | `123...abc` | ⚠️ For OAuth |

## ✅ Deployment Checklist

- [ ] Git repo pushed to GitHub
- [ ] `Procfile` exists
- [ ] `runtime.txt` exists
- [ ] `requirements.txt` updated
- [ ] `settings.py` has DATABASE_URL support
- [ ] SECRET_KEY generated
- [ ] Allowed hosts configured
- [ ] PostgreSQL database created in Railway
- [ ] Environment variables added to Railway
- [ ] Deploy triggered
- [ ] Logs checked for errors
- [ ] Superuser account created
- [ ] Admin panel accessible

---

**Questions? Check:**
- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.djangoproject.com/en/stable/howto/deployment/
