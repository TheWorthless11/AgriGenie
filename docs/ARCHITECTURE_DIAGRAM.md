# Super Admin User Management - Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SUPER ADMIN DASHBOARD                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         User Management (admin-panel/users/)             │  │
│  │                                                          │  │
│  │  ┌────────┬────────┬────────┬────────┬──────────────┐  │  │
│  │  │Username│ Email  │ Phone  │ Role   │ Status │View │  │  │
│  │  ├────────┼────────┼────────┼────────┼──────────────┤  │  │
│  │  │  john  │j@m.com │1234567 │Farmer  │ ACTIVE │ Show│  │  │
│  │  │  jane  │j@g.com │9876543 │Buyer   │BLOCKED │█ De│  │  │
│  │  └────────┴────────┴────────┴────────┴──────────────┘  │  │
│  │                                                          │  │
│  │                     [View Details]                       │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
└─────────────────────────────┼───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   USER DETAIL PAGE                              │
│  /admin-panel/users/<id>/details/                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [Profile Picture]                                       │  │
│  │  Username: john_farmer                                   │  │
│  │  Email: john@mail.com                                    │  │
│  │  Role: Farmer                                            │  │
│  │  Status: ✅ ACTIVE                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Farmer Profile:                                         │  │
│  │  • Farm: Green Acres                                     │  │
│  │  • Size: 50 acres                                        │  │
│  │  • Experience: 15 years                                  │  │
│  │  • Approval: ✅ Approved                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Documents:                                              │  │
│  │  ┌────────────────────────────────────────────────┐     │  │
│  │  │ Document Type  │ Details │ Action             │     │  │
│  │  ├────────────────┼─────────┼────────────────────┤     │  │
│  │  │ NID Number     │ 1234567 │ [View]             │     │  │
│  │  │ Approval Doc   │ File    │ [Download]         │     │  │
│  │  └────────────────┴─────────┴────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Admin Actions:                                          │  │
│  │                                                          │  │
│  │  [🚫 Block User]  [🗑️ Delete User]                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Action: Click "Block User"                                    │
│                        ▼                                        │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              BLOCK USER CONFIRMATION                            │
│   /admin-panel/users/<id>/block/                               │
│                                                                  │
│  ⚠️  BLOCK USER ACCOUNT                                         │
│                                                                  │
│  Username: john_farmer                                          │
│  Email: john@mail.com                                           │
│                                                                  │
│  ⚠️  WARNING: This user will be suspended from the platform     │
│                                                                  │
│  Reason for Blocking (Required):                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Suspicious activity detected                           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [✅ Confirm Block]  [❌ Cancel]                               │
│                                                                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                    User Blocked! ✅
                    is_active = False
                    blocked_reason recorded
                    blocked_date = Now
                    Notification sent to user
                          │
└─────────────────────────▼───────────────────────────────────────┐
│              USER BLOCKED - NEXT STEPS                          │
│                                                                  │
│  ❌ User cannot login                                            │
│  ❌ Active sessions terminated                                   │
│  ✅ Block reason: "Suspicious activity detected"                │
│  ✅ Blocked on: Nov 15, 2025 10:30 AM                           │
│  ✅ Can be unblocked anytime                                     │
│                                                                  │
│  [↩️ Back to Detail]  [↪️ Unblock User]                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘


```

## Data Flow Diagram

```
Registration Forms (Farmer/Buyer)
         │
         ▼
┌──────────────────────────────┐
│  Real-Time Validation (AJAX) │
└──────────────┬───────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
 /api/check-nid-   /api/check-company-
 uniqueness/       name/
      │                 │
      ▼                 ▼
   Check DB          Check DB
   NID Table         BuyerProfile
      │                 │
      └────────┬────────┘
               ▼
        Return JSON Response
        {available: bool}
               │
      ┌────────┴────────┐
      ▼                 ▼
   Duplicate         No Duplicate
   ❌ Disabled       ✅ Enabled
   Next Button       Next Button


User Management Flow
         │
         ▼
┌──────────────────────────────┐
│    User Management Table     │
│  /admin-panel/users/         │
└──────────────┬───────────────┘
               │
         [View Details]
               ▼
┌──────────────────────────────┐
│    User Detail View          │
│  /admin-panel/users/<id>/    │
│  details/                    │
└──────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   [Block User]  [Delete User]
        │
        ▼
   Block Form
   (Reason Required)
        │
        ▼
   Database Update:
   • is_blocked_by_admin = True
   • blocked_reason = <reason>
   • blocked_date = Now()
   • is_active = False
        │
        ▼
   Create Notification
        │
        ▼
   User Cannot Login ❌


Unblock Flow
         │
         ▼
   [Unblock User]
         │
         ▼
   Unblock Confirmation
         │
         ▼
   Database Update:
   • is_blocked_by_admin = False
   • is_active = True
         │
         ▼
   Create Notification
         │
         ▼
   User Can Login ✅
```

## Database Schema Changes

```
BEFORE:
┌─────────────────────────────┐
│   CustomUser                │
├─────────────────────────────┤
│ id                          │
│ username                    │
│ email                       │
│ phone_number                │
│ role (farmer/buyer/admin)   │
│ is_active                   │
│ date_joined                 │
│ ...                         │
└─────────────────────────────┘

┌──────────────────────────────┐
│   UserApproval               │
├──────────────────────────────┤
│ id                           │
│ user_id (FK)                 │
│ nid_number  ← NO CONSTRAINT  │
│ status                       │
│ ...                          │
└──────────────────────────────┘

AFTER:
┌──────────────────────────────────┐
│   CustomUser                     │
├──────────────────────────────────┤
│ id                               │
│ username                         │
│ email                            │
│ phone_number                     │
│ role (farmer/buyer/admin)        │
│ is_active                        │
│ date_joined                      │
│ is_blocked_by_admin      ← NEW   │
│ blocked_reason           ← NEW   │
│ blocked_date             ← NEW   │
│ ...                              │
└──────────────────────────────────┘

┌───────────────────────────────────┐
│   UserApproval                    │
├───────────────────────────────────┤
│ id                                │
│ user_id (FK)                      │
│ nid_number [UNIQUE, INDEX] ← MOD  │
│ status                            │
│ ...                               │
└───────────────────────────────────┘

┌────────────────────────────────────┐
│   BuyerProfile                     │
├────────────────────────────────────┤
│ id                                 │
│ user_id (FK)                       │
│ company_name [UNIQUE, INDEX] ← MOD │
│ business_type                      │
│ is_approved                        │
│ ...                                │
└────────────────────────────────────┘
```

## URL Routes Map

```
ADMIN PANEL ROUTES:
/admin-panel/
├── dashboard/                           → admin_dashboard
├── users/                               → user_management (list)
├── users/<id>/
│   ├── details/                         → user_detail_view ✨
│   ├── block/                           → block_user ✨
│   ├── unblock/                         → unblock_user ✨
│   ├── delete/                          → delete_user
│   └── toggle-approval/                 → toggle_user_approval
├── approvals/                           → user_approvals
├── crops/                               → crop_management
├── alerts/                              → system_alerts_admin
├── reports/                             → system_reports
├── ai-monitoring/                       → ai_monitoring
├── activity-logs/                       → activity_logs
├── irrigation/                          → irrigation_crops_admin
└── master-crops/                        → master_crops_list

API ROUTES:
/api/
├── check-nid-uniqueness/                → check_nid_uniqueness ✨ (AJAX)
└── check-company-name/                  → check_company_name_uniqueness ✨ (AJAX)

✨ = Newly Added
```

## Template Rendering Flow

```
admin-panel/user_management.html
    │
    ├─ Displays users table
    ├─ For each user: {% url 'user_detail_view' u.id %}
    │
    └─ Click "View Details"
         │
         ▼
         user_detail_view() function
         │
         ├─ Fetch user data
         ├─ Fetch profile (Farmer/Buyer)
         ├─ Fetch documents
         ├─ Calculate statistics
         │
         ▼
         admin-panel/user_detail_full.html
         │
         ├─ Display profile section
         ├─ Display documents section
         ├─ Display statistics
         │
         └─ Render buttons:
            ├─ Block User → block_user() → block_user_confirm.html
            ├─ Unblock User → unblock_user() → unblock_user_confirm.html
            └─ Delete User → delete_user()


Block/Unblock Flow:
    └─ admin-panel/block_user_confirm.html
        │
        └─ Form submission (POST)
            │
            ├─ Validate reason (required)
            ├─ Update database
            ├─ Create notification
            │
            └─ Redirect to user_detail_view()
```

## Authentication & Authorization

```
@login_required(login_url='login')
    ▼
User must be logged in
OR
Redirect to login page
    ▼
@user_passes_test(is_admin)
    ▼
User.is_admin must be True
OR
Access denied

Both decorators required on:
✓ user_detail_view()
✓ block_user()
✓ unblock_user()
✓ check_nid_uniqueness()
✓ check_company_name_uniqueness()
✓ check user deletion
✓ check user approval toggle
```

## Feature Summary Table

```
╔════════════════════╦═══════════════════════╦════════════════╗
║ Feature            ║ How It Works           ║ Location       ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ View Details       ║ Click button          ║ user_mgmt.html ║
║                    ║ → user_detail_view()  ║ detail_full.   ║
║                    ║                       ║ html            ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ View Documents     ║ Auto-fetched from DB  ║ user_detail_   ║
║                    ║ → Display in table    ║ full.html      ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ Block User         ║ Click button          ║ block_user()   ║
║                    ║ → Form (reason req.)  ║ block_confirm. ║
║                    ║ → Update DB           ║ html            ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ Unblock User       ║ Click button          ║ unblock_user() ║
║                    ║ → Confirmation       ║ unblock_       ║
║                    ║ → Update DB           ║ confirm.html   ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ NID Uniqueness     ║ AJAX on blur/change   ║ check_nid_     ║
║                    ║ → /api/check-nid...   ║ uniqueness()   ║
║                    ║ → Disable btn        ║ js (to add)    ║
╠════════════════════╬═══════════════════════╬════════════════╣
║ Company Name       ║ AJAX on blur/change   ║ check_company_ ║
║ Uniqueness         ║ → /api/check-company  ║ name_()        ║
║                    ║ → Disable btn        ║ js (to add)    ║
╚════════════════════╩═══════════════════════╩════════════════╝
```

## Deployment Checklist Flow

```
Code Ready ✓
    │
    ▼
Code Review ✓
    │
    ▼
Unit Tests ✓
    │
    ▼
Integration Tests ✓
    │
    ▼
Backup Database
    │
    ▼
Run Migrations
  • python manage.py makemigrations
  • python manage.py migrate
    │
    ▼
Clear Cache (if applicable)
    │
    ▼
Smoke Tests
    │
    ▼
Monitor Error Logs
    │
    ▼
✅ DEPLOYMENT COMPLETE
```

