# 🌾 Mandatory Crops System - Complete Guide

## Overview

AgriGenie has been configured with **three mandatory crops** that all farmers must select from when listing crops for sale. This ensures data consistency and improves the platform's ability to provide accurate recommendations and predictions.

---

## ✅ Configured Crops

### 1. **Potato** 🥔
- **Category**: Vegetables
- **Type**: Conventional
- **Status**: Active ✅
- **Description**: Starchy vegetable widely grown and traded

### 2. **Tomato** 🍅
- **Category**: Vegetables
- **Type**: Conventional
- **Status**: Active ✅
- **Description**: Widely used vegetable in cooking

### 3. **Rice** 🌾
- **Category**: Grains
- **Type**: Conventional
- **Status**: Active ✅
- **Description**: Staple grain crop

---

## 🏗️ System Architecture

### Database Structure

```
Admin Panel (admin_panel.MasterCrop)
    ├── Potato (id: 1, is_active: True)
    ├── Tomato (id: 2, is_active: True)
    └── Rice (id: 3, is_active: True)
            ↓
Farmer Crops (farmer.Crop)
    ├── Foreign Key → master_crop
    ├── Farmer 1 → Potato listing 1
    ├── Farmer 1 → Tomato listing 2
    └── Farmer 2 → Rice listing 3
            ↓
Supporting Systems
    ├── Price Prediction (uses master_crop)
    ├── Disease Detection (uses master_crop)
    ├── Weather Alerts (location-based)
    └── Order Management (links to crop listings)
```

### Implementation Details

**Master Crop Model** (`admin_panel/models.py`)
```python
class MasterCrop(models.Model):
    crop_name = models.CharField(max_length=100, unique=True)
    crop_type = models.CharField(max_length=50, choices=CROP_TYPES)
    category = models.CharField(max_length=50, choices=CROP_CATEGORIES)
    is_active = models.BooleanField(default=True)  # Control availability
    created_by = models.ForeignKey(CustomUser, ...)
    # ... other fields
```

**Crop Model** (`farmer/models.py`)
```python
class Crop(models.Model):
    farmer = models.ForeignKey(CustomUser, ...)
    master_crop = models.ForeignKey('admin_panel.MasterCrop', on_delete=models.PROTECT)
    quantity = models.FloatField()
    price_per_unit = models.FloatField()
    # ... other farmer-specific fields
```

---

## 👥 User Roles

### Admin Panel

**Location**: `/admin/` → Admin authentication required

**Capabilities**:
- View all Master Crops
- Edit crop details (name, type, category, description)
- Activate/deactivate crops (`is_active` toggle)
- Add new crops to the system
- View which farmers are using each crop
- Cannot delete crops (PROTECT foreign key maintains data integrity)

**How to Access**:
```
1. Go to http://localhost:8000/admin/
2. Login with admin credentials
3. Click "Master Crop Templates" in left sidebar
4. View, edit, or add crops
```

### Farmers

**Location**: `/farmer/` (after login)

**Capabilities**:
- Select ONLY from the 3 active crops
- Post listings for selected crops
- View price predictions (based on selected crop)
- Check disease detection (based on selected crop)
- Receive weather alerts (location-based)
- Trade with other farmers

**Workflow**:
```
1. Farmer logs in → /farmer/dashboard/
2. Click "Add New Crop"
3. Form appears with dropdown (only 3 crops shown)
4. Select Potato, Tomato, or Rice
5. Fill in quantity, price, location, etc.
6. Submit listing
7. Crop appears in marketplace
```

---

## 🔧 Technical Implementation

### Data Migration

**File**: `admin_panel/migrations/0004_add_mandatory_crops.py`

**What it does**:
```python
# Forward migration: Creates 3 crops
crops_data = [
    {'crop_name': 'Potato', 'category': 'vegetables', ...},
    {'crop_name': 'Tomato', 'category': 'vegetables', ...},
    {'crop_name': 'Rice', 'category': 'grains', ...},
]
for crop in crops_data:
    MasterCrop.objects.create(**crop)

# Reverse migration: Deletes 3 crops
MasterCrop.objects.filter(crop_name__in=['Potato', 'Tomato', 'Rice']).delete()
```

**To Apply**:
```bash
python manage.py migrate admin_panel
```

**To Reverse** (only if needed):
```bash
python manage.py migrate admin_panel 0003_farmerlisting
```

### Form Integration

**File**: `farmer/forms.py`

```python
class CropForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active crops
        self.fields['master_crop'].queryset = MasterCrop.objects.filter(is_active=True)
```

**What it does**:
- Automatically filters dropdown to only active crops
- If admin marks crop as `is_active=False`, it disappears from dropdown
- Farmers cannot create crops with inactive crops

### Views

**File**: `farmer/views.py` (price_prediction & disease_detection views)

```python
# View automatically uses selected master_crop
crop = Crop.objects.get(id=crop_id)
predictions = predict_prices_with_ml(crop)  # Uses crop's master_crop
```

---

## 📊 Database Status

### Verify Crops are Created

```bash
# Terminal command to check
python manage.py shell -c "from admin_panel.models import MasterCrop; \
    crops = MasterCrop.objects.all(); \
    [print(f'{c.crop_name} - {c.get_category_display()} - Active: {c.is_active}') for c in crops]"
```

**Expected Output**:
```
Potato - Vegetables - Active: True
Rice - Grains - Active: True
Tomato - Vegetables - Active: True
```

### Count Total Crops

```bash
python manage.py shell -c "from admin_panel.models import MasterCrop; \
    print(f'Total crops: {MasterCrop.objects.count()}')"
```

---

## 🎯 Use Cases

### Use Case 1: Add a New Crop Type

**Scenario**: Admin wants to add "Wheat" as a new crop

**Steps**:
1. Go to `/admin/`
2. Click "Master Crop Templates"
3. Click "Add Master Crop Template"
4. Fill in:
   - Crop Name: **Wheat**
   - Crop Type: **Conventional**
   - Category: **Grains**
   - Description: **Optional**
   - Is Active: **True** ✓
5. Click "Save"
6. Wheat now appears in farmer's crop dropdown

### Use Case 2: Disable a Crop

**Scenario**: Admin wants to disable Tomato temporarily

**Steps**:
1. Go to `/admin/`
2. Click "Master Crop Templates"
3. Click "Tomato"
4. Uncheck **Is Active**
5. Click "Save"
6. Tomato disappears from farmer's dropdown
7. Existing Tomato listings remain in database (no data loss)
8. Farmers cannot create NEW Tomato listings

### Use Case 3: View Listings for a Crop

**Scenario**: Admin wants to see all Tomato listings

**Steps**:
1. Go to `/admin/`
2. Click "Master Crop Templates"
3. Click "Tomato"
4. Scroll to "Listings" section
5. Shows all farms that posted Tomato crops
6. Click on any listing to view details

---

## ⚠️ Important Constraints

### Cannot Delete Crops (By Design)

**Reason**: Foreign Key protection (`on_delete=models.PROTECT`)

```python
# In farmer/models.py
master_crop = models.ForeignKey('admin_panel.MasterCrop', 
                                on_delete=models.PROTECT)  # ← Prevents deletion
```

**What happens if you try to delete**:
```
ProtectedError: Cannot delete ... because it has references from 'farmer.crop'
```

**Solution**: Mark as `is_active=False` instead of deleting

### Only Active Crops Show in Dropdown

**Behavior**:
```python
# farmer/forms.py automatically filters
self.fields['master_crop'].queryset = MasterCrop.objects.filter(is_active=True)
```

**Result**:
- Farmers see only active crops in dropdown
- Inactive crops don't appear in form
- Existing listings with inactive crops remain visible (no data loss)

---

## 🔍 Troubleshooting

### Issue: New crop not showing in dropdown

**Check**:
1. Go to `/admin/` → Master Crop Templates
2. Click the crop
3. Verify **Is Active** is checked ✓

**Solution**: Check the `is_active` field

### Issue: Cannot delete crop from admin

**Check**: This is intentional! Crops cannot be deleted.

**Solution**: Mark as `is_active=False` instead

### Issue: Old crop still appears in listing

**Check**: It's probably deactivated but old listings still exist

**Solution**: Admin can delete specific Crop listings (not MasterCrop)

### Issue: Farmer created crop with deleted master_crop

**Status**: Cannot happen - system prevents it with `on_delete=models.PROTECT`

---

## 📈 Performance Considerations

### Query Optimization

**Current Implementation**:
```python
# Efficient: Single query with filtering
MasterCrop.objects.filter(is_active=True)
```

**With 3 mandatory crops**:
- Very fast: < 1ms per query
- Minimal database load
- Perfect for dropdown rendering

### Scalability

**Can we add more crops?**
- **Yes!** Scale to 10-20 crops without performance impact
- **Recommendation**: Keep it under 50 crops for best UX

**Can we make crops dynamic?**
- **Yes!** Admin can add new crops anytime
- **No database migration needed** for new crops after initial setup

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `admin_panel/models.py` | MasterCrop model definition |
| `admin_panel/migrations/0004_add_mandatory_crops.py` | Data migration that creates the 3 crops |
| `farmer/models.py` | Crop model (references MasterCrop) |
| `farmer/forms.py` | CropForm filters to active crops |
| `farmer/views.py` | Views that use selected master_crop |
| `admin_panel/admin.py` | Admin panel configuration |
| `templates/farmer/add_crop.html` | Form template for farmers |

---

## 🚀 Quick Commands

### Check Crops in Database
```bash
python manage.py shell -c "from admin_panel.models import MasterCrop; \
    [print(f'{c.id}: {c.crop_name}') for c in MasterCrop.objects.all()]"
```

### Count Listings per Crop
```bash
python manage.py shell -c "from admin_panel.models import MasterCrop; \
    [print(f'{c.crop_name}: {c.listings.count()} listings') \
     for c in MasterCrop.objects.all()]"
```

### Create New Crop via Shell
```bash
python manage.py shell
>>> from admin_panel.models import MasterCrop
>>> crop = MasterCrop.objects.create(
...     crop_name='Wheat',
...     crop_type='conventional',
...     category='grains',
...     is_active=True
... )
>>> print(f"Created: {crop.crop_name}")
```

### Deactivate a Crop
```bash
python manage.py shell
>>> from admin_panel.models import MasterCrop
>>> crop = MasterCrop.objects.get(crop_name='Tomato')
>>> crop.is_active = False
>>> crop.save()
>>> print("Tomato deactivated")
```

---

## ✅ Verification Checklist

- [x] 3 mandatory crops created in database
- [x] All crops marked as `is_active=True`
- [x] Farmer dropdown shows only these 3 crops
- [x] Admin can activate/deactivate crops
- [x] Cannot delete crops (prevented by foreign key)
- [x] Price prediction works with selected crop
- [x] Disease detection works with selected crop
- [x] No data loss when crops marked inactive
- [x] Django system check passes (0 issues)
- [x] Server running successfully

---

## 🎓 Best Practices

### For Admin

1. **Keep crops active** unless truly unavailable
2. **Don't delete crops** - use `is_active=False`
3. **Add crop images** via generic_image field
4. **Document** any new crops in a changelog
5. **Monitor** which crops are most used

### For Developers

1. **Always filter** by `is_active=True` in forms
2. **Use foreign keys** to prevent orphaned data
3. **Log changes** when adding/removing crops
4. **Test thoroughly** before activating new crops
5. **Backup database** before bulk changes

---

## 📞 Support

**Questions or issues?** Check:
1. [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - Overall system status
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
3. Django Admin Docs - `/admin/doc/` (if installed)

**Direct Django Shell Debug**:
```bash
python manage.py shell
>>> from admin_panel.models import MasterCrop
>>> MasterCrop.objects.all().values()
```

---

**Last Updated**: February 9, 2026
**Status**: ✅ Production Ready
**Version**: 1.0
