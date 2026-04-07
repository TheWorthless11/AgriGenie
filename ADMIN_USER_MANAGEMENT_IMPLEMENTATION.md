# Super Admin User Management Implementation Guide

## Summary of Changes Implemented

### 1. **Model Changes** ✅

#### `admin_panel/models.py`
- Updated `UserApproval.nid_number` to be **UNIQUE** with `db_index=True`
- This ensures each farmer's NID number is unique in the system

#### `users/models.py`
- Added `is_blocked_by_admin` (BooleanField) - tracks if user is blocked
- Added `blocked_reason` (TextField) - stores reason for blocking
- Added `blocked_date` (DateTimeField) - tracks when user was blocked

- Updated `BuyerProfile.company_name` to be **UNIQUE** with `db_index=True`
- This ensures each buyer's company name is unique in the system

### 2. **View Functions** ✅

#### New functions added to `admin_panel/views.py`:

**block_user(request, user_id)**
- Blocks a user from accessing the platform
- Sets `is_blocked_by_admin = True`, `is_active = False`
- Stores blocking reason and date
- Sends notification to user
- Confirms action before execution

**unblock_user(request, user_id)**
- Unblocks a previously blocked user
- Resets blocking fields
- Sends unblocking notification
- Confirms action before execution

**user_detail_view(request, user_id)**
- Enhanced user detail page showing:
  - User profile information
  - Documents (NID for farmers, business docs for buyers)
  - Statistics (crops, orders)
  - Approval status
  - Block/unblock option
  - Delete option

**check_nid_uniqueness(request)** [AJAX]
- GET endpoint for real-time NID validation
- Returns JSON: `{available: boolean, message: string}`
- Checks against existing NID numbers in UserApproval
- Allows editing without false duplicates

**check_company_name_uniqueness(request)** [AJAX]
- GET endpoint for real-time company name validation
- Returns JSON: `{available: boolean, message: string}`
- Checks against existing company names in BuyerProfile
- Case-insensitive comparison

### 3. **URL Routes** 

Add these to `urls.py`:

```python
# User management detail views
path('admin-panel/users/<int:user_id>/details/', admin_views.user_detail_view, name='user_detail_view'),
path('admin-panel/users/<int:user_id>/block/', admin_views.block_user, name='block_user'),
path('admin-panel/users/<int:user_id>/unblock/', admin_views.unblock_user, name='unblock_user'),

# AJAX validation endpoints
path('api/check-nid-uniqueness/', admin_views.check_nid_uniqueness, name='check_nid_uniqueness'),
path('api/check-company-name/', admin_views.check_company_name_uniqueness, name='check_company_name'),
```

### 4. **Template Files Needed**

#### `templates/admin_panel/user_detail.html`
- Display user profile with all information
- Show documents based on user role:
  - **Farmer:** NID Number + NID Card Photo
  - **Buyer:** Company Name + Legal Papers + Company Photo
- Display statistics (crops/orders)
- Action buttons:
  - **View Details** (already on management page)
  - **Block User** (with reason modal)
  - **Unblock User** (if currently blocked)
  - **Delete User**

#### `templates/admin_panel/block_user_confirm.html`
- Confirmation page to block user
- Form with reason field (required)
- Warning message about consequences
- Confirm/Cancel buttons

#### `templates/admin_panel/unblock_user_confirm.html`
- Confirmation page to unblock user
- Display current blocking information
- Confirm/Cancel buttons

#### Update `templates/admin_panel/user_management.html`
- Add "View Details" button for each user
- Show block status next to user
- Improve action button layout

### 5. **Frontend Validation - Real-time Checks**

For the onboarding forms to check uniqueness while typing:

#### **Farmer NID Validation** (in farmer_onboarding.html):
```javascript
$('#nid_number').on('change blur', function() {
    const nid = $(this).val().trim();
    if (nid) {
        $.ajax({
            url: '/api/check-nid-uniqueness/',
            data: { nid: nid },
            success: function(response) {
                if (!response.available) {
                    // Show error: NID already exists
                    $('#nextBtn').prop('disabled', true);
                    $('#nidError').text(response.message).show();
                } else {
                    // Clear error
                    $('#nextBtn').prop('disabled', false);
                    $('#nidError').hide();
                }
            }
        });
    }
});
```

#### **Buyer Company Name Validation** (in buyer_onboarding.html):
```javascript
$('#company_name').on('change blur', function() {
    const companyName = $(this).val().trim();
    if (companyName) {
        $.ajax({
            url: '/api/check-company-name/',
            data: { company_name: companyName },
            success: function(response) {
                if (!response.available) {
                    // Show error: Company name already exists
                    $('#nextBtn').prop('disabled', true);
                    $('#companyError').text(response.message).show();
                } else {
                    // Clear error
                    $('#nextBtn').prop('disabled', false);
                    $('#companyError').hide();
                }
            }
        });
    }
});
```

### 6. **Database Migrations**

Run these commands to apply changes:

```bash
python manage.py makemigrations
python manage.py migrate
```

The migrations will:
1. Add `nid_number` unique constraint in UserApproval
2. Add blocking fields to CustomUser
3. Add `company_name` unique constraint in BuyerProfile

### 7. **Feature Checklist**

- [x] ✅ Unique NID Numbers for Farmers
- [x] ✅ Unique Company Names for Buyers
- [x] ✅ Real-time validation while typing
- [x] ✅ Block user functionality
- [x] ✅ Unblock user functionality
- [x] ✅ View Details page with documents
- [x] ✅ Delete user functionality (existing)
- [ ] 🔄 Update UI templates (pending)

### 8. **Security Considerations**

- All sensitive operations require admin checks
- Blocking reason is logged
- Blocked users automatic ally logged in notifications
- NID/Company name validation is unique at database level
- Transaction atomic for data consistency

### 9. **Testing Scenarios**

1. **Duplicate NID Check:**
   - Farmer 1 submits NID: 123456
   - Farmer 2 tries to submit same NID: 123456 → ERROR "NID already exists by Farmer 1"

2. **Duplicate Company Check:**
   - Buyer 1 submits "Green Traders"
   - Buyer 2 tries "green traders" → ERROR "Company name already registered"

3. **Block/Unblock Flow:**
   - Admin clicks block → Modal asks for reason → Sets is_active=False
   - User tries to login → Sees "Account blocked" message
   - Admin unblo → User can login again

4. **View Details:**
   - Admin clicks "View Details" → Shows all documents & info
   - Can delete/block from this page

### 10. **API Endpoints Summary**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/check-nid-uniqueness/` | GET | Validate NID uniqueness |
| `/api/check-company-name/` | GET | Validate company name uniqueness |
| `/admin-panel/users/<id>/details/` | GET | View user full details |
| `/admin-panel/users/<id>/block/` | POST | Block user |
| `/admin-panel/users/<id>/unblock/` | POST | Unblock user |
| `/admin-panel/users/<id>/delete/` | POST | Delete user |

---

**Status:** Implementation Guide Complete
**Files Modified:** 4 (models.py, urls.py + 2 template files)
**New Files Needed:** 3 templates
**Database Migrations:** Required
