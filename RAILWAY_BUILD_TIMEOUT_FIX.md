# Railway Build Timeout Fix Guide

## ⚠️ Problem: Build Timed Out

Your build failed with **"Build timed out"** during the Docker import step. This happens because:

1. **110 packages** in requirements.txt (including heavy ML libraries)
2. Installation takes **3+ minutes** just for pip
3. Railway's build timeout is **~15 minutes**
4. Network latency + compilation adds more time

---

## ✅ SOLUTION - 3 Steps to Fix

### **Step 1: Optimize Dockerfile** 
Update to use gunicorn instead of daphne (lighter):

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN mkdir -p staticfiles media && python manage.py collectstatic --noinput || true

CMD ["gunicorn", "asgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "2"]
```

### **Step 2: Create railway.json**

```json
{
  "build": {
    "buildpacks": [
      {
        "url": "heroku/python"
      }
    ]
  },
  "deploy": {
    "startCommand": "gunicorn asgi:application --bind 0.0.0.0:$PORT --workers 2"
  }
}
```

### **Step 3: Update Procfile**

```
release: python manage.py migrate
web: gunicorn asgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## 🔧 Optional: Reduce Package Size

If still timing out, **comment out heavy packages** in requirements.txt:

**Comment these (not essential for Railway):**
```
# tensorflow>=2.17
# keras>=3.0
# torch>=2.5
# torchvision>=0.20
# torchaudio>=2.5
# numpy>=1.26 (keep it)
# scikit-learn>=1.5
```

These are heavy ML libraries. Railway free tier (512MB RAM) struggles with them.

---

## 📝 Update Your Files

### **File 1: Dockerfile**
Replace Daphne with Gunicorn (lighter, faster to build)

### **File 2: Create railway.json** 
Copy the code above

### **File 3: Update Procfile**
Use web: gunicorn instead of daphne

---

## 🚀 Steps to Retry Deployment on Railway

1. **Push changes to GitHub:**
```bash
git add Dockerfile railway.json Procfile
git commit -m "Optimize Railway deployment - fix build timeout"
git push
```

2. **In Railway Dashboard:**
   - Click your **web service**
   - Click **Deployments** tab
   - Click **Retry Deploy** button

3. **Watch the logs:**
   - Should complete in **5-8 minutes** now
   - Look for: `Listening on 0.0.0.0:8000`

---

## ❌ If Still Timing Out

**Option A: Split requirements.txt**

Create `requirements-production.txt` with only essential packages:

```
Django==4.2.29
djangorestframework==3.14.0
django-cors-headers==4.2.0
django-celery-beat==2.5.0
django-celery-results==2.5.1
gunicorn==21.2.0
psycopg2-binary==2.9.9
python-decouple==3.8
dj-database-url==2.1.0
whitenoise==6.5.0
channels==4.3.2
daphne==4.2.1
django-allauth==65.14.3
redis==5.0.1
celery==5.3.1
pillow==10.1.0
# ... other essential packages
```

Then update Dockerfile to use it.

**Option B: Use Railway's PostgreSQL without Redis**

Remove Celery/Redis from requirements for free tier:
- No background tasks
- No WebSocket scaling
- App will still work!

---

## 📊 Build Optimization Summary

| Issue | Solution |
|-------|----------|
| **Too many packages** | Use `requirements-production.txt` |
| **Daphne is heavy** | Switch to Gunicorn |
| **Long install time** | Add `.dockerignore` files |
| **ML libraries** | Comment out TensorFlow, PyTorch |
| **Build timeout** | Use railway.json to configure |

---

## ✅ Deployment Checklist

- [ ] Updated Dockerfile (Gunicorn instead of Daphne)
- [ ] Created railway.json
- [ ] Updated Procfile
- [ ] Pushed to GitHub
- [ ] Clicked "Retry Deploy" on Railway
- [ ] Build completes in < 10 minutes
- [ ] App shows "Listening on 0.0.0.0:8000"

---

## 🆘 Still Having Issues?

**Check Railway logs for:**
```
ERROR: Could not find a version that satisfies the requirement
timeout during package download
Out of memory
```

**Solutions:**
- Remove heavy packages from requirements.txt
- Use smaller Python image (slim is already set)
- Check if any package has complex dependencies

---

**Ready? Push your changes and retry! 🚀**
