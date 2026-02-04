# AgriGenie - Quick Reference Guide

## 📖 Documentation Index

Quick links to all project documentation:

### Setup & Installation
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Step-by-step installation
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Production deployment
- **.env.example** - Environment configuration template

### Features & Usage
- **[FEATURE_DOCUMENTATION.md](FEATURE_DOCUMENTATION.md)** - Detailed feature descriptions
- **[README.md](README.md)** - Project overview
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - REST API endpoints
- **[TEMPLATES_GUIDE.md](TEMPLATES_GUIDE.md)** - Template structure

### Project Status
- **[FEATURE_AUDIT_REPORT.md](FEATURE_AUDIT_REPORT.md)** - Pre-completion audit
- **[PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md)** - Full completion report
- **[COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)** - This session's work

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database
python manage.py migrate
python manage.py createsuperuser

# 3. Start development server
python manage.py runserver

# In separate terminals:
celery -A AgriGenie worker -l info
celery -A AgriGenie beat -l info
```

Access: http://localhost:8000

---

## 👥 User Accounts to Create

### Test Accounts for Development

```bash
# Create these users for testing
python manage.py createsuperuser

# Then create in web UI:
# 1. Farmer Account
#    - Username: farmer_test
#    - Email: farmer@test.com
#    - Password: test123456

# 2. Buyer Account
#    - Username: buyer_test
#    - Email: buyer@test.com
#    - Password: test123456

# 3. Admin Account (via createsuperuser)
#    - Username: admin
#    - Email: admin@test.com
#    - Password: admin123456
```

---

## 🔑 Key Features at a Glance

### For Farmers
| Feature | URL | How to Access |
|---------|-----|---------------|
| Dashboard | /farmer/dashboard/ | Login as farmer |
| Add Crop | /farmer/add-crop/ | Click "Add Crop" |
| Disease Detection | /farmer/disease-detection/ | Upload crop image |
| Price Prediction | /farmer/price-prediction/ | View price trends |
| Weather Alerts | /farmer/weather-alerts/ | Real-time alerts |
| Orders Received | /farmer/orders/ | Manage orders |
| Messages | /farmer/messages/ | View/send messages |

### For Buyers
| Feature | URL | How to Access |
|---------|-----|---------------|
| Dashboard | /buyer/dashboard/ | Login as buyer |
| Marketplace | /buyer/marketplace/ | Browse crops |
| Search | /search/ | Search & filter |
| Orders | /buyer/orders/ | Track orders |
| Wishlist | /buyer/wishlist/ | Saved crops |

### For Admin
| Feature | URL | How to Access |
|---------|-----|---------------|
| Dashboard | /admin-panel/dashboard/ | Admin login |
| Approvals | /admin-panel/approvals/ | Approve users |
| Crops | /admin-panel/crops/ | Manage listings |
| Reports | /admin-panel/reports/ | View analytics |

---

## 🛠️ Common Tasks

### Add a New Crop (as Farmer)

1. Login as farmer
2. Go to "My Crops" → "Add New Crop"
3. Fill in:
   - Crop name (e.g., "Tomato")
   - Crop type (e.g., "Vegetable")
   - Quantity & unit (e.g., 100 kg)
   - Price per unit (e.g., ৳45)
   - Location
   - Harvest & availability dates
   - Upload crop image
4. Click "Add Crop"

### Detect Crop Disease (as Farmer)

1. Go to "Disease Detection"
2. Select a crop
3. Upload crop/leaf image
4. Click "Analyze Image"
5. View disease name, confidence, and treatment

### Place an Order (as Buyer)

1. Go to "Marketplace"
2. Search or browse crops
3. Click on crop
4. Click "Place Order"
5. Enter quantity and delivery date
6. Submit

### Approve Farmers (as Admin)

1. Login as admin
2. Go to Admin Panel → "User Approvals"
3. Review pending farmers
4. Click "Approve" or "Reject"

---

## 🐛 Troubleshooting

### Issue: Celery tasks not running

**Solution:**
```bash
# Make sure Redis is running
redis-server

# Restart Celery
celery -A AgriGenie worker -l info
celery -A AgriGenie beat -l info
```

### Issue: Disease detection not working

**Solution:**
```bash
# Install TensorFlow
pip install tensorflow==2.14.0

# Or CPU-only version
pip install tensorflow-cpu==2.14.0

# Restart Django
python manage.py runserver
```

### Issue: Weather API not working

**Solution:**
1. Get free API key: https://openweathermap.org/api
2. Add to `.env`: `WEATHER_API_KEY=your_key_here`
3. Restart Django server

### Issue: Database migration error

**Solution:**
```bash
# Rollback and retry
python manage.py migrate --fake-initial

# Or check migration status
python manage.py migrate --plan
```

---

## 📊 Database Models Quick Reference

### User Models
- `CustomUser` - Base user with role
- `FarmerProfile` - Farmer-specific details
- `BuyerProfile` - Buyer-specific details

### Crop & Order Models
- `Crop` - Farmer's produce
- `Order` - Buyer order
- `CropDisease` - Disease detection record
- `CropPrice` - Price predictions

### Notification Models
- `Notification` - System alerts
- `Message` - User-to-user messages
- `WeatherAlert` - Weather alerts

### Admin Models
- `UserApproval` - Farmer verification
- `SystemAlert` - System announcements
- `ActivityLog` - User activity tracking

---

## 🔗 Useful Endpoints

### Public Endpoints
```
GET  /                           - Home page
POST /register/                  - User registration
POST /login/                     - User login
GET  /marketplace/               - Marketplace home
GET  /search/                    - Search crops
```

### Authenticated Endpoints
```
GET  /farmer/dashboard/          - Farmer dashboard
POST /farmer/add-crop/           - Create crop
POST /farmer/disease-detection/  - Analyze image
GET  /buyer/marketplace/         - Buyer marketplace
POST /buyer/place-order/<id>/    - Place order
```

### Admin Endpoints
```
GET  /admin-panel/dashboard/     - Admin dashboard
GET  /admin-panel/approvals/     - User approvals
GET  /admin-panel/crops/         - Crop management
GET  /admin-panel/reports/       - Reports
```

---

## 📱 Response Formats

### Disease Detection Response
```json
{
  "disease_name": "Early Blight",
  "disease_type": "fungal",
  "confidence": 87.5,
  "treatment": "Remove infected leaves and apply fungicide",
  "model_used": "mobilenetv2"
}
```

### Price Prediction Response
```json
{
  "predictions": [
    {"date": "2026-01-14", "price": 45.50, "day": 1},
    {"date": "2026-01-15", "price": 46.23, "day": 2}
  ],
  "best_sell_date": "2026-02-10",
  "best_price": 52.75
}
```

### Order Response
```json
{
  "id": 1,
  "crop_id": 5,
  "buyer_id": 10,
  "quantity": 50,
  "total_price": 2275.00,
  "status": "pending",
  "created_at": "2026-01-13T10:30:00Z"
}
```

---

## 🔐 Security Quick Checks

Before deployment:
- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use strong database password
- [ ] Enable HTTPS
- [ ] Set up backup strategy
- [ ] Configure firewall
- [ ] Enable security headers

---

## 📈 Performance Tips

1. **Database:**
   - Use select_related() for foreign keys
   - Use prefetch_related() for M2M
   - Add indexes on searched fields

2. **Caching:**
   - Redis is configured
   - Cache frequently accessed data
   - Use Django cache framework

3. **Files:**
   - Compress images on upload
   - Use CDN for static files
   - Limit upload file sizes

4. **API:**
   - Paginate large result sets
   - Implement rate limiting
   - Use pagination for listings

---

## 📚 Learning Resources

### Django Documentation
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/

### TensorFlow
- https://www.tensorflow.org/tutorials
- https://keras.io/

### Celery
- https://docs.celeryproject.org/

### Bootstrap
- https://getbootstrap.com/docs/

---

## 💬 Support

### Getting Help
1. Check relevant documentation file
2. Review code comments
3. Check error logs
4. See troubleshooting section above

### Reporting Issues
When reporting issues, include:
- What you did
- What you expected
- What actually happened
- Error message (if any)
- Environment info (OS, Python version, etc.)

---

## 🔄 Regular Maintenance

### Daily
- Monitor error logs
- Check database health
- Verify backups

### Weekly
- Update dependencies
- Review failed tasks
- Analyze usage stats

### Monthly
- Security updates
- Performance optimization
- Database maintenance

---

## 📞 Quick Commands

```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests (when available)
python manage.py test

# Django shell
python manage.py shell

# Start Celery worker
celery -A AgriGenie worker -l info

# Start Celery Beat
celery -A AgriGenie beat -l info

# Flush database (development only!)
python manage.py flush

# Reset specific app
python manage.py migrate app_name zero

# Generate fake data
python manage.py seed_data  # if available
```

---

## 🎯 Success Checklist

- [ ] Environment configured (.env file created)
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] Database migrated (python manage.py migrate)
- [ ] Superuser created (python manage.py createsuperuser)
- [ ] Django server running (python manage.py runserver)
- [ ] Celery worker running (celery -A AgriGenie worker)
- [ ] Celery Beat running (celery -A AgriGenie beat)
- [ ] Can access web application (http://localhost:8000)
- [ ] Can login as admin
- [ ] Can create test farmer/buyer accounts

**If all checked: Project is ready to use!** ✅

---

*Last Updated: January 13, 2026*  
*Version: 1.0.0*
