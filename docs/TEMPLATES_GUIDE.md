# AgriGenie Frontend Templates Documentation

## Overview
This document provides a complete guide to all HTML templates created for the AgriGenie project. The templates are built with Bootstrap 5 and are responsive across all devices.

## Template Structure

```
templates/
├── base.html                          # Base template with navbar and footer
├── home.html                          # Homepage with hero and features
├── users/
│   ├── register.html                  # User registration form
│   ├── login.html                     # User login form
│   ├── profile.html                   # User profile view (pending)
│   ├── profile_edit.html              # User profile editor (pending)
│   ├── dashboard.html                 # Generic user dashboard (pending)
│   └── notifications.html             # Notifications view (pending)
├── farmer/
│   ├── dashboard.html                 # Farmer dashboard with stats
│   ├── crops_list.html                # List of farmer's crops (pending)
│   ├── crop_form.html                 # Add/edit crop form (pending)
│   ├── orders_list.html               # Farmer's orders (pending)
│   ├── order_detail.html              # Order details (pending)
│   ├── disease_detection.html         # Disease detection tool (pending)
│   ├── price_prediction.html          # Price prediction display (pending)
│   ├── weather_alerts.html            # Weather alerts (pending)
│   ├── messages.html                  # Messaging interface (pending)
│   └── ratings.html                   # Farmer ratings view (pending)
├── buyer/
│   ├── dashboard.html                 # Buyer dashboard with stats
│   ├── marketplace.html               # Marketplace browse (pending - mapped to marketplace/home.html)
│   ├── crop_detail.html               # Crop detail page (pending)
│   ├── orders_list.html               # Buyer's orders (pending)
│   ├── order_detail.html              # Order details (pending)
│   ├── wishlist.html                  # Wishlist view (pending)
│   ├── saved_crops.html               # Saved crops (pending)
│   └── purchase_history.html          # Purchase history (pending)
├── marketplace/
│   ├── home.html                      # Marketplace homepage with filters
│   ├── search_results.html            # Search results (pending)
│   ├── farmer_storefront.html         # Farmer storefront view (pending)
│   ├── trending_crops.html            # Trending crops section (pending)
│   └── top_rated.html                 # Top rated crops (pending)
├── admin_panel/
│   ├── dashboard.html                 # Admin dashboard with stats
│   ├── user_management.html           # User management interface (pending)
│   ├── user_detail.html               # User detail view (pending)
│   ├── user_approvals.html            # Pending user approvals (pending)
│   ├── crop_management.html           # Crop moderation (pending)
│   ├── crop_detail.html               # Crop detail admin view (pending)
│   ├── system_alerts.html             # System alerts management (pending)
│   ├── system_reports.html            # Analytics and reports (pending)
│   ├── ai_monitoring.html             # AI model monitoring (pending)
│   └── activity_logs.html             # Activity logging (pending)
└── errors/
    ├── 404.html                       # 404 page (pending)
    └── 500.html                       # 500 page (pending)

static/
├── css/
│   └── style.css                      # Custom CSS styling
├── js/
│   └── main.js                        # Main JavaScript functions
└── images/                            # Image assets (pending)
```

## Completed Templates (11 files)

### 1. **base.html** - Foundation Template
- **Location:** `templates/base.html`
- **Purpose:** Base template extending to all pages
- **Features:**
  - Responsive Bootstrap 5 navbar
  - User authentication dropdown
  - Role-based navigation (Farmer, Buyer, Admin)
  - Flash message display
  - Footer with links
  - Static file loading
- **Context Variables:**
  - `user` - Currently authenticated user
  - `unread_notifications` - Count of unread notifications
- **Blocks:**
  - `title` - Page title
  - `extra_css` - Additional CSS files
  - `content` - Page content
  - `extra_js` - Additional JavaScript

### 2. **home.html** - Homepage
- **Location:** `templates/home.html`
- **Purpose:** Public landing page
- **Features:**
  - Hero section with call-to-action
  - Feature cards highlighting key benefits
  - "How It Works" section with 3 steps
  - Testimonials from users
  - Final CTA section
  - Responsive design
- **Context Variables:** None required
- **Links:** Register, Login, Dashboard, Marketplace

### 3. **register.html** - Registration Form
- **Location:** `templates/users/register.html`
- **Purpose:** New user registration
- **Features:**
  - Email validation
  - Username field
  - Full name field
  - Role selection (Farmer/Buyer)
  - Password strength requirements
  - Password confirmation
  - Error message display
  - Bootstrap form styling
- **Context Variables:**
  - `form` - Django registration form
- **Form Fields:**
  - Email
  - Username
  - First Name
  - Role (Radio buttons)
  - Password
  - Confirm Password

### 4. **login.html** - Login Form
- **Location:** `templates/users/login.html`
- **Purpose:** User authentication
- **Features:**
  - Username/Email field
  - Password field
  - Remember me checkbox
  - Error message display
  - Demo credentials info
  - Bootstrap styling
  - Responsive layout
- **Context Variables:**
  - `form` - Django authentication form
- **Form Fields:**
  - Username
  - Password
  - Remember Me

### 5. **farmer/dashboard.html** - Farmer Dashboard
- **Location:** `templates/farmer/dashboard.html`
- **Purpose:** Farmer home page with statistics
- **Features:**
  - Key statistics cards:
    - Active Crops count
    - Pending Orders count
    - Unread Messages count
    - Farm Rating
  - Quick actions sidebar
  - Farm information card
  - Recent orders table
  - Crops listing table
  - Status indicators
  - Edit/View buttons
- **Context Variables:**
  - `farmer_profile` - FarmerProfile object
  - `crops_count` - Integer
  - `orders_count` - Integer
  - `unread_messages` - Integer
  - `recent_orders` - QuerySet
  - `recent_crops` - QuerySet
- **Status Badges:** Pending, Confirmed, Shipped, Delivered, Available, Sold Out

### 6. **buyer/dashboard.html** - Buyer Dashboard
- **Location:** `templates/buyer/dashboard.html`
- **Purpose:** Buyer home page with statistics
- **Features:**
  - Key statistics cards:
    - Active Orders
    - Wishlist Items
    - Saved Crops
    - Total Spent
  - Quick actions sidebar
  - Profile information card
  - Active orders table
  - Wishlist preview table
  - Status tracking
  - Action buttons
- **Context Variables:**
  - `buyer_profile` - BuyerProfile object
  - `active_orders_count` - Integer
  - `wishlist_count` - Integer
  - `saved_crops_count` - Integer
  - `total_spent` - Float
  - `active_orders` - QuerySet
  - `wishlist_items` - QuerySet

### 7. **admin_panel/dashboard.html** - Admin Dashboard
- **Location:** `templates/admin_panel/dashboard.html`
- **Purpose:** Administrative control panel
- **Features:**
  - Key statistics cards:
    - Total Users
    - Pending Approvals
    - Total Crops
    - System Alerts
  - Management quick links
  - System health monitoring
  - Pending approvals table
  - Recent system alerts table
  - Additional 7-day statistics
  - Status indicators
- **Context Variables:**
  - `total_users` - Integer
  - `pending_approvals` - Integer
  - `total_crops` - Integer
  - `system_alerts` - Integer
  - `pending_users` - QuerySet
  - `recent_alerts` - QuerySet
  - `new_users_7days` - Integer
  - `new_crops_7days` - Integer
  - `total_transactions` - Integer

### 8. **marketplace/home.html** - Marketplace
- **Location:** `templates/marketplace/home.html`
- **Purpose:** Browse and search crops
- **Features:**
  - Search functionality
  - Category filters (Vegetables, Fruits, Grains, Spices)
  - Price range filter
  - Sorting options (Newest, Price, Rating)
  - Featured farmers section
  - Products grid display (responsive 3-4 columns)
  - Wishlist button on each product
  - Pagination
  - Out of stock indicators
  - Farmer ratings display
- **Context Variables:**
  - `crops` - Paginated crop listings
  - `wishlist_count` - Integer
  - `search` - Search term string
  - `selected_categories` - List
  - `min_price`, `max_price` - Integers
  - `sort` - Sort option string
  - `featured_farmers` - QuerySet
  - `page_obj` - Pagination object
- **Filters:** Search, Category, Price, Sort
- **AJAX:** Wishlist toggle without page reload

### 9. **style.css** - Custom Styling
- **Location:** `static/css/style.css`
- **Size:** ~500 lines
- **Features:**
  - CSS variables for colors
  - General body and link styles
  - Navbar customization
  - Hero section styling
  - Card hover effects
  - Button styling and states
  - Form styling and focus states
  - Badge styling
  - Table styling
  - Alert animations
  - Dashboard stat cards
  - Step numbers styling
  - Footer styling
  - Responsive adjustments for mobile
  - Animation keyframes
  - Loading state indicators
  - Utility classes
- **Color Scheme:**
  - Primary: Green (#28a745)
  - Secondary: Gray (#6c757d)
  - Danger: Red (#dc3545)
  - Info: Cyan (#17a2b8)
  - Warning: Amber (#ffc107)

### 10. **main.js** - JavaScript Utilities
- **Location:** `static/js/main.js`
- **Size:** ~450 lines
- **Functions Implemented:**
  - `initializeTooltips()` - Bootstrap tooltip init
  - `autoCloseAlerts()` - Auto-dismiss alerts
  - `initializeFormValidation()` - Form validation
  - `initializeNotifications()` - Notification updates
  - `refreshNotifications()` - AJAX notification refresh
  - `deleteItem()` - Confirm delete with modal
  - `addToWishlist()` - AJAX wishlist add
  - `removeFromWishlist()` - AJAX wishlist remove
  - `markNotificationAsRead()` - Mark notification as read
  - `showNotification()` - Display toast notification
  - `getCookie()` - Get CSRF token
  - `formatCurrency()` - Currency formatting
  - `formatDate()` - Date formatting
  - `debounce()` - Function debouncing
  - `searchCrops()` - Real-time search
  - `filterByCategory()` - Category filtering
  - `filterByPrice()` - Price range filtering
  - `previewImage()` - Image preview on upload
  - `toggleFormField()` - Show/hide form fields
  - `copyToClipboard()` - Copy text to clipboard
  - `exportTableToCSV()` - Export table data
  - `downloadCSV()` - CSV file download
  - `setupRealtimeValidation()` - Live form validation
  - `validateField()` - Single field validation
  - `scrollToElement()` - Smooth scroll
  - `goToPage()` - Pagination navigation
- **AJAX Functions:** Wishlist, Notifications, Filtering
- **Bootstrap Integration:** Alert, Modal, Tooltip

## Pending Templates (27 files)

The following templates are designed but not yet created. They are ready for implementation based on the completed examples:

### Users App (4 pending)
- `templates/users/profile.html`
- `templates/users/profile_edit.html`
- `templates/users/dashboard.html` (role-based)
- `templates/users/notifications.html`

### Farmer App (7 pending)
- `templates/farmer/crops_list.html`
- `templates/farmer/crop_form.html`
- `templates/farmer/orders_list.html`
- `templates/farmer/order_detail.html`
- `templates/farmer/disease_detection.html`
- `templates/farmer/price_prediction.html`
- `templates/farmer/weather_alerts.html` (+ more)

### Buyer App (7 pending)
- `templates/buyer/crop_detail.html`
- `templates/buyer/orders_list.html`
- `templates/buyer/order_detail.html`
- `templates/buyer/wishlist.html`
- `templates/buyer/saved_crops.html`
- `templates/buyer/purchase_history.html`

### Marketplace App (4 pending)
- `templates/marketplace/search_results.html`
- `templates/marketplace/farmer_storefront.html`
- `templates/marketplace/trending_crops.html`
- `templates/marketplace/top_rated.html`

### Admin Panel App (6 pending)
- `templates/admin_panel/user_management.html`
- `templates/admin_panel/user_approvals.html`
- `templates/admin_panel/crop_management.html`
- `templates/admin_panel/system_alerts.html`
- `templates/admin_panel/system_reports.html`
- `templates/admin_panel/activity_logs.html`

### Error Pages (2 pending)
- `templates/errors/404.html`
- `templates/errors/500.html`

## Template Features Summary

### Bootstrap Components Used
- Navbar with dropdowns
- Cards with hover effects
- Tables with responsive design
- Forms with validation
- Alerts and badges
- Pagination
- Modals (ready for JS)
- Progress bars
- Grid layout system
- Responsive images

### Styling Approach
- Bootstrap 5 classes
- Custom CSS variables
- Responsive design (mobile-first)
- Smooth animations
- Hover effects
- Status-based colors
- Icon integration (Font Awesome)

### JavaScript Features
- AJAX form submission
- Real-time validation
- Wishlist toggle
- Notification auto-refresh
- Search debouncing
- Image preview
- CSV export
- Clipboard copy
- Pagination navigation

### Security Features
- CSRF token in forms
- Form validation
- Input sanitization ready
- Permission checks in views

## Installation & Setup

### 1. Static Files Configuration
The static files are configured in `settings.py`:
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 2. Running the Server
```bash
python manage.py runserver
```

### 3. Collect Static Files (Production)
```bash
python manage.py collectstatic
```

### 4. Template Loading
Django loads templates from:
- `templates/` - Base templates
- `templates/{app_name}/` - App-specific templates

## Browser Compatibility
- Chrome/Edge 88+
- Firefox 87+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Responsive Breakpoints
Using Bootstrap 5 breakpoints:
- xs: < 576px (mobile)
- sm: ≥ 576px (small devices)
- md: ≥ 768px (tablets)
- lg: ≥ 992px (desktops)
- xl: ≥ 1200px (large screens)

## Next Steps

1. **Complete Pending Templates:** Create the remaining 27 templates following the pattern established
2. **Add Dashboard Redirects:** Update `users/views.py` to redirect to role-specific dashboards
3. **Implement Image Uploads:** Add image handling for crop photos
4. **Add PDF Export:** For orders and reports
5. **Enhance Animations:** Add page transition effects
6. **Mobile Optimization:** Test and refine mobile layout
7. **Accessibility:** Add ARIA labels and keyboard navigation
8. **Dark Mode:** Optional dark theme support

## Template Mapping to Views

| Template | View Function | Path |
|----------|---------------|------|
| home.html | home | / |
| register.html | register | /users/register/ |
| login.html | login_view | /users/login/ |
| farmer/dashboard.html | farmer_dashboard | /users/dashboard/ |
| buyer/dashboard.html | buyer_dashboard | /users/dashboard/ |
| admin_panel/dashboard.html | admin_dashboard | /admin/dashboard/ |
| marketplace/home.html | marketplace_home | /marketplace/ |

## Version History
- **v1.0** (Current) - Created 11 core templates with Bootstrap 5 and custom CSS
  - Base template with navbar and footer
  - Authentication pages (login, register)
  - 3 Role-specific dashboards (Farmer, Buyer, Admin)
  - Marketplace browsing interface
  - Custom styling and JavaScript utilities

---

**Last Updated:** 2026-01-15
**Template Count:** 11/38 (29% Complete)
**Status:** Ready for Development
