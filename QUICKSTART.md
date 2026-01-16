# AgriGenie - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+
- Redis Server
- Git

### Step 1: Setup (2 minutes)
```bash
# Clone and setup
cd AgriGenie
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python manage.py migrate
python manage.py init_ai_monitoring
python manage.py createsuperuser  # Create admin account
```

### Step 2: Start Services (2 minutes)

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
```
→ Access at http://localhost:8000

**Terminal 2 - Redis:**
```bash
redis-server
```

**Terminal 3 - Celery Worker (optional):**
```bash
celery -A AgriGenie worker -l info
```

### Step 3: Login (1 minute)

1. Go to http://localhost:8000
2. Click "Register"
3. Choose role (Farmer or Buyer)
4. Fill details and submit
5. Go to http://localhost:8000/admin
6. Approve your registration
7. Login!

---

## 📚 Feature Quick Access

### For Farmers 👨‍🌾

| Feature | URL | Purpose |
|---------|-----|---------|
| Add Crop | `/farmer/add-crop/` | List crops for sale |
| My Crops | `/farmer/crops/` | Manage crops |
| Disease Detection | `/farmer/disease-detection/` | AI analyze leaf images |
| Price Prediction | `/farmer/price-prediction/` | See 30-day forecast |
| Weather Alerts | `/farmer/weather-alerts/` | Disaster warnings |
| Orders | `/farmer/orders/` | Track buyer orders |
| Messages | `/farmer/messages/` | Chat with buyers |

### For Buyers 👨‍💼

| Feature | URL | Purpose |
|---------|-----|---------|
| Marketplace | `/buyer/marketplace/` | Browse crops |
| Search | `/search/?q=tomato` | Find specific crops |
| My Orders | `/buyer/orders/` | Track purchases |
| Wishlist | `/buyer/wishlist/` | Save favorites |
| Messages | `/farmer/messages/` | Contact farmers |

### For Admins 👨‍💻

| Feature | URL | Purpose |
|---------|-----|---------|
| Dashboard | `/admin-panel/dashboard/` | View stats |
| User Approvals | `/admin-panel/approvals/` | Approve users |
| Crop Management | `/admin-panel/crops/` | Monitor listings |
| AI Monitoring | `/admin-panel/ai-monitoring/` | Check model accuracy |
| Reports | `/admin-panel/reports/` | Generate reports |
| Activity Logs | `/admin-panel/activity-logs/` | Track actions |
| System Alerts | `/admin-panel/alerts/` | Send alerts |

---

## 🧪 Test Scenarios

### Scenario 1: Farmer Workflow
```
1. Register as Farmer → farmer1 / test@test.com
2. Admin approves registration → /admin/
3. Update farm profile → /profile/edit/
4. Add crop → /farmer/add-crop/
5. Wait for orders → /farmer/orders/
6. Use AI features → /farmer/disease-detection/
```

### Scenario 2: Buyer Workflow
```
1. Register as Buyer → buyer1 / buyer@test.com
2. Admin approves
3. Browse marketplace → /buyer/marketplace/
4. Search crops → /search/?q=tomato
5. Add to wishlist → Click "Add to Wishlist"
6. Place order → /crop/{id}/
7. Track order → /buyer/orders/
```

### Scenario 3: Admin Workflow
```
1. Login as superuser
2. Go to /admin/
3. Approve pending users
4. Monitor crops → /admin-panel/crops/
5. Check AI accuracy → /admin-panel/ai-monitoring/
6. Send system alerts → /admin-panel/alerts/
```

---

## 🎯 Key Features to Try

### 1. **AI Disease Detection** 🤖
```
1. Login as farmer
2. Go to /farmer/disease-detection/
3. Select a crop
4. Upload any leaf/plant image
5. See AI analysis with confidence score
6. Read treatment recommendations
```

### 2. **Price Prediction** 📈
```
1. Login as farmer
2. Go to /farmer/price-prediction/
3. Select a crop
4. View interactive 30-day price chart
5. Check "Best Sell Date" recommendation
6. Analyze market volatility
```

### 3. **Real-time Weather** 🌤️
```
1. Login as farmer
2. Go to /farmer/weather-alerts/
3. View current weather
4. Check disaster alerts
5. Read preparedness guides
```

### 4. **Smart Search** 🔍
```
1. Login as buyer
2. Go to /search/
3. Enter: crop name, location, price range
4. Apply multiple filters
5. Sort results
6. View matching crops
```

---

## 🛠️ Troubleshooting

### Issue: "No module named django"
```bash
source venv/bin/activate
pip install django
```

### Issue: "Redis connection error"
```bash
# Start Redis in another terminal
redis-server
```

### Issue: "Port 8000 in use"
```bash
python manage.py runserver 8080
```

### Issue: "Database not found"
```bash
python manage.py migrate
python manage.py init_ai_monitoring
```

---

## 📊 Admin Commands

```bash
# Create superuser
python manage.py createsuperuser

# Initialize AI monitoring
python manage.py init_ai_monitoring

# Run migrations
python manage.py migrate

# Create test data
python manage.py shell
# Then in shell:
from users.models import CustomUser
CustomUser.objects.create_user(
    username='test',
    email='test@test.com',
    password='test123',
    role='farmer'
)

# View logs
tail -f logs/django.log

# Run tests
python manage.py test
```

---

## 📱 API Quick Examples

### Get Crops
```bash
curl http://localhost:8000/api/crops/?location=Punjab
```

### Create Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{"crop_id": 1, "quantity": 50}'
```

### Analyze Disease
```bash
curl -X POST http://localhost:8000/api/disease-detection/ \
  -F "crop_id=1" \
  -F "disease_image=@image.jpg"
```

### Get Price Prediction
```bash
curl http://localhost:8000/api/crops/1/price-prediction/?days=30
```

---

## 🎓 Learning Resources

- **README.md** - Full project overview
- **INSTALLATION_GUIDE.md** - Detailed setup instructions
- **FEATURE_DOCUMENTATION.md** - Complete feature guide
- **API_DOCUMENTATION.md** - API reference
- **TEMPLATES_GUIDE.md** - Template customization

---

## 🔐 Security Notes

1. Change `SECRET_KEY` in production
2. Set `DEBUG = False` in production
3. Use strong passwords
4. Enable HTTPS in production
5. Keep dependencies updated
6. Regular backups

---

## 📈 Next Steps

1. ✅ Explore the marketplace
2. ✅ Test AI features
3. ✅ Try weather alerts
4. ✅ Place a test order
5. ✅ Review admin panel
6. ✅ Check documentation
7. ✅ Customize templates
8. ✅ Deploy to production

---

## 💬 Help & Support

- **Issues**: Check GitHub issues
- **Email**: support@agrigenie.com
- **Docs**: https://agrigenie.readthedocs.io
- **Forum**: https://forum.agrigenie.com

---

## 🎉 You're All Set!

Your AgriGenie instance is now running with all features:

✅ User Management
✅ Crop Management
✅ AI Disease Detection
✅ Price Prediction
✅ Weather Integration
✅ Notifications
✅ Messaging
✅ Orders
✅ Admin Panel
✅ Analytics & Reports

**Happy farming! 🌾**

---

## Quick URL Reference

| Page | URL |
|------|-----|
| Home | http://localhost:8000/ |
| Login | http://localhost:8000/login/ |
| Register | http://localhost:8000/register/ |
| Dashboard | http://localhost:8000/dashboard/ |
| Admin | http://localhost:8000/admin/ |
| Marketplace | http://localhost:8000/buyer/marketplace/ |
| Farmer Dashboard | http://localhost:8000/farmer/ |
| Buyer Dashboard | http://localhost:8000/buyer/ |

---

**Version**: 1.0.0
**Last Updated**: January 13, 2026
**Status**: Production Ready
