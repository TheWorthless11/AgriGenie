# Test Framework Architecture & Maintenance

## 📐 Architecture Overview

The AgriGenie test framework is organized into **5 layers** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│  Test Files (Unit & Integration Tests)              │
│  ├── test_models.py        (30+ tests)              │
│  ├── test_views.py         (20+ tests)              │
│  ├── test_forms.py         (15+ tests)              │
│  ├── test_integration.py   (20+ tests)              │
│  └── test_ai_and_utils.py  (15+ tests)              │
├─────────────────────────────────────────────────────┤
│  Fixtures & Setup (conftest.py)                     │
│  ├── User fixtures (farmer_user, buyer_user, ...)  │
│  ├── Profile fixtures (farmer_profile, ...)        │
│  ├── Data fixtures (crop, master_crop, ...)        │
│  └── Admin fixtures (admin_user, ...)              │
├─────────────────────────────────────────────────────┤
│  Configuration (pytest.ini, setup.cfg)              │
│  ├── Test discovery patterns                       │
│  ├── Markers (unit, integration, slow, etc)        │
│  ├── Coverage settings                             │
│  └── Output formatting                             │
├─────────────────────────────────────────────────────┤
│  Django/Pytest Integration                          │
│  ├── Django DB setup                               │
│  ├── Transaction handling                          │
│  └── Client/Request fixtures                       │
└─────────────────────────────────────────────────────┘
```

---

## 📁 File Structure & Purpose

### 1. **conftest.py** - Test Fixtures Hub
**Purpose**: Centralized test data generation
**Scope**: Available to all test modules

```python
# Core User Fixtures
farmer_user()        # Creates farmer with PIN auth
buyer_user()         # Creates buyer with password
admin_user()         # Creates superuser

# Profile Fixtures
farmer_profile()     # Links to farmer_user
buyer_profile()      # Links to buyer_user

# Data Fixtures
master_crop()        # Creates MasterCrop (Tomato)
crop()              # Creates active Crop listing

# Example: Using fixtures
def test_example(farmer_user, crop):
    assert crop.farmer == farmer_user
```

### 2. **test_models.py** - Model Unit Tests
**Purpose**: Test database models in isolation
**Coverage**: 11 model classes, 30+ test cases

**Organization:**
```python
class TestCustomUserModel:
    # Tests for custom authentication
    # PIN validation, location, blocking features

class TestFarmerProfile:
    # Tests for farmer-specific data
    # Ratings, approvals, verification

class TestCrop:
    # Tests for crop listings
    # Availability, pricing, validation

class TestOrder/ChatRoom/etc:
    # Tests for each major model
```

**Test Pattern:**
```python
@pytest.mark.django_db
def test_create_farmer():
    user = CustomUser.objects.create_user(...)
    assert user.role == 'farmer'
```

### 3. **test_views.py** - View/Endpoint Tests
**Purpose**: Test HTTP endpoints and access control
**Coverage**: 20+ test cases across 6 view groups

**Organization:**
```python
class TestAuthenticationViews:
    # /register/, /login/, /logout/

class TestFarmerViews:
    # /farmer/dashboard/, /farmer/crops/, etc

class TestBuyerViews:
    # /buyer/marketplace/, /buyer/dashboard/, etc

class TestAdminViews:
    # /admin/, user management, approvals

class TestPublicPages:
    # /, /about/, /contact/

class TestAPIViews:
    # /api/crops/, /api/users/, etc
```

**Test Pattern:**
```python
def test_farmer_dashboard_requires_login(client):
    response = client.get('/farmer/dashboard/')
    assert response.status_code == 302  # Redirect to login
```

### 4. **test_forms.py** - Form Validation Tests
**Purpose**: Test form input validation
**Coverage**: 5 form classes, 15+ test cases

**Organization:**
```python
class TestDynamicRegistrationForm:
    # Farmer PIN validation
    # Buyer password validation
    # Required field validation

class TestCropForm:
    # Price/quantity validation
    # Quality grade validation
    # File upload validation

class TestPurchaseRequestForm:
    # Quantity validation
    # Optional message handling
```

**Test Pattern:**
```python
def test_valid_farmer_registration():
    form = DynamicRegistrationForm(data={
        'pin': '1234',
        'confirm_pin': '1234',
        ...
    })
    assert form.is_valid()
```

### 5. **test_integration.py** - End-to-End Workflow Tests
**Purpose**: Test complete user journeys
**Coverage**: 7 major workflows, 20+ test cases

**Organization:**
```python
class TestUserRegistrationWorkflow:
    # Farmer: Sign up → Verify → Approve → Active
    # Buyer: Sign up → Email verification → Active

class TestCropListingAndSearchWorkflow:
    # Farmer posts crop → Buyer searches → Finds crop

class TestPurchaseWorkflow:
    # Request → Farmer accepts → Order created → Delivered

class TestMessagingWorkflow:
    # Create chat room → Send messages → Verify receipt

class TestOrderLifecycleWorkflow:
    # Complete order status transitions (Pending→Delivered→Completed)
```

**Test Pattern:**
```python
def test_complete_purchase_workflow(farmer_user, buyer_user, crop):
    # Setup
    pr = PurchaseRequest.objects.create(crop=crop, buyer=buyer_user, ...)
    
    # Workflow
    pr.accept()
    order = Order.objects.create(purchase_request=pr, ...)
    order.mark_delivered()
    
    # Verify
    assert order.status == 'completed'
```

### 6. **test_ai_and_utils.py** - AI & Utility Tests
**Purpose**: Test AI models and helper functions
**Coverage**: 13 test classes, 40+ test cases

**Organization:**
```python
class TestPricePredictionModel:
    # ML model accuracy
    # Input validation
    # Prediction output

class TestDiseaseDetectionModel:
    # Image classification
    # Confidence scores
    # Error handling

class TestEmailUtilities:
    # Email sending
    # Template rendering
    # Error handling

class TestDataValidation:
    # Phone number format
    # Email validation
    # Price validation
```

---

## 🔄 Test Execution Flow

### Single Test Execution
```
User runs: pytest tests/test_models.py::TestCrop::test_create_crop

↓

pytest discovers test file

↓

conftest.py fixtures loaded into memory

↓

test_create_crop() executes with setup/teardown

↓

Database transaction rolled back automatically

↓

Test result reported (PASSED/FAILED)
```

### Full Suite Execution
```
pytest with no arguments

↓

Discovers all test_*.py files in tests/

↓

Loads conftest.py once for all tests

↓

Executes 100+ tests:
  ├── test_models.py (35 tests)
  ├── test_views.py (20 tests)
  ├── test_forms.py (15 tests)
  ├── test_integration.py (20 tests)
  └── test_ai_and_utils.py (10 tests)

↓

Database cleaned between each test (via @pytest.mark.django_db)

↓

Final report: X passed, Y failed, Z skipped
```

---

## 🛠️ Adding New Tests

### Adding a Model Test
```python
# In test_models.py

class TestNewModel:
    """Test the NewModel class"""
    
    @pytest.mark.django_db
    def test_create_new_model(self):
        # Arrange
        obj = NewModel.objects.create(field1='value1')
        
        # Act
        result = obj.some_method()
        
        # Assert
        assert result == expected
```

### Adding an Integration Test
```python
# In test_integration.py

class TestNewWorkflow:
    """Test new user workflow"""
    
    @pytest.mark.django_db
    def test_workflow_name(self, farmer_user, buyer_user):
        # Step 1: Setup
        obj = Model.objects.create(user=farmer_user, ...)
        
        # Step 2: Execute
        obj.do_something()
        
        # Step 3: Verify
        assert obj.status == 'expected'
        
        # Step 4: Continue workflow
        # ... more assertions
```

### Adding a View Test
```python
# In test_views.py

def test_new_view_access(self, authenticated_user):
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    response = client.get('/path/to/view/')
    
    assert response.status_code == 200
    assert 'expected_content' in response.content
```

---

## 📊 Fixture Architecture

### Fixture Dependency Graph
```
farmer_user (core fixture)
    ├── master_crop (depends on nothing)
    │   └── crop (depends on farmer_user + master_crop)
    │
    └── farmer_profile (depends on farmer_user)

buyer_user (core fixture)
    ├── buyer_profile (depends on buyer_user)
    │   
    └── [uses crop from farmer_user workflow]

admin_user (standalone fixture)
```

### Fixture Scope
```python
@pytest.fixture  # function scope (reset per test)
def farmer_user():
    return CustomUser.objects.create_user(...)

@pytest.fixture(scope='module')  # reset per module
def expensive_fixture():
    return expensive_setup()
```

---

## ✅ Quality Metrics

### Coverage Goals
```
├── Models:           90% target (highest impact)
├── Views:            85% target (HTTP handling)
├── Forms:            85% target (validation)
├── Integration:      80% target (workflows)
├── Utilities:        75% target (helpers)
└── Overall Project:  80% target
```

### Performance Targets
```
Test Type              Average Time    Target
─────────────────────────────────────────────
Unit test             10-50ms         <100ms
Integration test      100-500ms       <1s
View test            50-200ms         <500ms
Full suite           5-10s            <15s
```

---

## 🔧 Maintenance Tasks

### Weekly
- [ ] Run full test suite: `pytest`
- [ ] Check coverage: `pytest --cov=.`
- [ ] Review failed tests
- [ ] Update for new code

### Monthly
- [ ] Audit test quality
- [ ] Remove obsolete tests
- [ ] Optimize slow tests
- [ ] Update documentation

### Before Release
- [ ] Run full suite 3+ times
- [ ] Generate coverage report
- [ ] Test with different Python versions
- [ ] Test with different Django versions

---

## 🐛 Common Maintenance Patterns

### Pattern 1: Model Changes
When you add a field to a model:
```python
# Add fixture update
@pytest.fixture
def crop(farmer_user):
    return Crop.objects.create(
        ...
        new_field='new_value'  # Add this
    )

# Add validation test
def test_new_field_validation(self):
    # Test new field constraints
```

### Pattern 2: View Changes
When you modify a view:
```python
# Update existing test or add new one
def test_view_modified_behavior(self):
    # Test new behavior
    # Remove test for old behavior
```

### Pattern 3: Form Changes
When you change form fields:
```python
# Update form test fixture data
# Add validation tests for new fields
# Update integration tests that use the form
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Test Database Not Cleaning
```python
# Solution: Use @pytest.mark.django_db
@pytest.mark.django_db
def test_something():
    pass

# Or use transactions
@pytest.mark.django_db(transaction=True)
def test_something():
    pass
```

### Issue 2: Fixture Not Resetting
```python
# Solution: Change fixture scope
@pytest.fixture
def data():
    return create_data()  # Fresh per test

# Instead of
@pytest.fixture(scope='module')
def data():  # Shared across all tests in module
    return create_data()
```

### Issue 3: Slow Tests
```bash
# Solution: Identify slow tests
pytest --durations=10

# Then optimize with:
# 1. Use setUp fixtures instead of creating in test
# 2. Use database.TransactionTestCase only when needed
# 3. Use mocks for external services
# 4. Cache expensive operations
```

---

## 📈 Test Metrics Dashboard

Track these metrics over time:

```
Metric                    Current    Target    Trend
───────────────────────────────────────────────────
Total Test Cases          100+       150+      ↑
Coverage Percentage       75%        80%       ↑
Avg Test Duration         50ms       <100ms    ↓
Slowest Test              2.5s       <1s       ↓
Test Execution Time       9s         <15s      ↓
Failing Tests             0          0         ✓
Skipped Tests             5          0         ↑
```

Monitor in CI/CD and alert on regressions.

---

## 🎓 Learning Resources

### For Test Writers
- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing Guide](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Pytest-Django Docs](https://pytest-django.readthedocs.io/)

### For TDD Practitioners
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)
- [Writing Testable Code](https://testing.googleblog.com/)
- [Test Pyramid Concept](https://martinfowler.com/bliki/TestPyramid.html)

---

## 🔐 Test Data Security

### ⚠️ Important: Never use real data in tests
```python
# ❌ BAD - Real user data
user = CustomUser.objects.create_user(
    phone_number='+8801712345678',  # Real phone!
    email='realuser@gmail.com'      # Real email!
)

# ✅ GOOD - Fake test data
from faker import Faker
fake = Faker()
user = CustomUser.objects.create_user(
    phone_number=fake.phone_number(),
    email=fake.email()
)
```

### Security Checklist
- [ ] No real user emails in tests
- [ ] No real phone numbers
- [ ] No real API keys or tokens
- [ ] No real passwords (use hashers)
- [ ] Use faker for random data
- [ ] Use model-bakery for complex data

---

## ✨ Best Practices Summary

| Aspect | Best Practice |
|--------|-----------------|
| **Test Names** | Clearly describe what is being tested |
| **Assertions** | One logical assertion per test (can have multiple asserts) |
| **Setup** | Use fixtures, not setup methods |
| **Cleanup** | Automatic via pytest fixtures |
| **Isolation** | Each test independent, no dependencies |
| **Speed** | Unit tests <100ms, integration tests <1s |
| **Coverage** | >80% overall, >90% for critical paths |
| **Documentation** | Docstrings for complex tests |
| **Organization** | Group related tests in classes |
| **Maintainability** | Avoid duplication, use fixtures |

---

**Version**: 1.0
**Last Updated**: April 2026
**Maintained by**: AgriGenie Development Team

For questions or improvements, please [create an issue](../issues) or contact the development team.
