# AgriGenie Superadmin Setup Guide

## Admin Account Created ✓

Your superadmin account has been successfully created with the following credentials:

### **Login Credentials**
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@agrigenie.local`

### **Admin Login URL**
```
http://127.0.0.1:8000/admin/
```

---

## 🔐 Security Features

The custom admin interface includes several security features:

1. **Non-Django Interface** - The login page doesn't reveal that this is a Django project
2. **Professional Branding** - Styled with AgriGenie branding and colors
3. **Activity Logging** - All admin actions are logged (login, logout, approvals, etc.)
4. **Session Management** - Secure session handling with optional "Remember Device" option

---

## 📋 Admin Dashboard Features

Once logged in, the admin has access to:

### **User Management**
- View all users (farmers, buyers, admins)
- Approve/reject user registrations
- View user details and activities
- Delete user accounts
- Toggle user approval status

### **Crop Management**
- View all crop listings
- Remove inappropriate crops
- View crop details and statistics
- Monitor crop quality and availability

### **System Alerts & Reports**
- Monitor system alerts
- View user reports
- Track activity logs
- Generate system reports

### **AI Monitoring**
- Monitor disease detection AI performance
- Monitor price prediction AI accuracy
- View AI processing statistics

### **Settings**
- Configure general system settings
- Manage notification preferences
- Setup security settings
- Configure AI features
- Manage system-wide parameters

---

## 🚀 First-Time Setup Steps

### Step 1: Start the Development Server
```bash
python manage.py runserver
```

### Step 2: Navigate to Admin Login
Open your browser and go to:
```
http://127.0.0.1:8000/admin/
```

### Step 3: Enter Your Credentials
- Username: `admin`
- Password: `admin123`

### Step 4: Check "Remember this device" (optional)
This will keep you logged in on this device

### Step 5: Click "Sign In to Dashboard"

---

## 🔄 Create Additional Admins

To create additional admin accounts, use the management command:

```bash
python manage.py create_superadmin --username [username] --password [password] --email [email]
```

**Example:**
```bash
python manage.py create_superadmin --username admin2 --password secure123 --email admin2@agrigenie.local
```

---

## 📝 Admin Activity Logging

All admin activities are automatically logged, including:
- Login attempts (successful and failed)
- Logout events
- User approvals/rejections
- Crop removals
- Settings changes
- Account modifications

**Access Activity Logs:**
Navigate to `Admin Panel → Activity Logs` to view the complete audit trail.

---

## 🔒 Recommended Security Practices

1. **Change Default Password**
   - Log in and navigate to Profile Settings
   - Change the default password immediately

2. **Set Up 2FA (if available)**
   - Enable two-factor authentication in security settings

3. **Limit Admin Access**
   - Only share admin credentials with trusted team members
   - Create individual admin accounts for each team member

4. **Monitor Activity Logs**
   - Regularly review admin activity logs
   - Watch for unauthorized access attempts

5. **Backup Credentials**
   - Store admin credentials in a secure password manager
   - Don't hardcode credentials in code

---

## 🛠️ Troubleshooting

### Issue: "Invalid username or password"
- Verify you're using `admin` and `admin123`
- Check if the database has been migrated: `python manage.py migrate`

### Issue: "Access denied. Only administrators can access this panel"
- Ensure the account has been created with the `create_superadmin` command
- Verify the user's role is set to 'admin'

### Issue: Admin page not loading
- Make sure Django development server is running
- Check for any error messages in the terminal
- Verify the URL is correct: `http://127.0.0.1:8000/admin/`

---

## 📱 Admin Panel Features

### Responsive Design
The admin panel is fully responsive and works on:
- ✓ Desktop (1920x1080 and higher)
- ✓ Tablet (768px and up)
- ✓ Mobile (320px and up)

### Modern UI
- Gradient design with AgriGenie branding
- Smooth animations and transitions
- Professional form styling
- Clear error messages
- Loading indicators

---

## 🔑 Default Admin URL Paths

| Feature | URL |
|---------|-----|
| Admin Login | `/admin/` |
| Admin Logout | `/admin/logout/` |
| Admin Dashboard | `/admin/dashboard/` |
| User Approvals | `/admin-panel/approvals/` |
| Crop Management | `/admin-panel/crops/` |
| System Alerts | `/admin-panel/alerts/` |
| Activity Logs | `/admin-panel/activity-logs/` |
| Settings | `/admin-panel/settings/` |

---

## 📞 Support

For issues or questions about the admin panel:
1. Check the Activity Logs for error details
2. Review the Django console for server-side errors
3. Verify all migrations are applied: `python manage.py migrate`
4. Ensure the Django development server is running

---

## ✅ Verification Checklist

- [x] Superadmin user created
- [x] Custom login page styled
- [x] Admin URL configured at `/admin/`
- [x] Activity logging enabled
- [x] Admin dashboard accessible
- [x] Non-Django interface appearance

**Status: Setup Complete ✓**

Login now at: **http://127.0.0.1:8000/admin/**
