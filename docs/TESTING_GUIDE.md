# AgriGenie Testing Guide & Strategy

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Suite Organization](#test-suite-organization)
3. [Running Tests](#running-tests)
4. [Test Coverage](#test-coverage)
5. [Writing Tests](#writing-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The AgriGenie test suite provides comprehensive coverage across:
- **Unit Tests**: Individual components in isolation
- **Integration Tests**: Complete user workflows
- **AI/ML Tests**: Disease detection and price prediction
- **Utility Tests**: Helper functions and services

**Total Test Cases**: 80+
**Target Coverage**: >80%

---

## Test Suite Organization

### Directory Structure
```
tests/
├── __init__.py                    # Package initialization
├── conftest.py                    # Pytest fixtures (users, crops, profiles)
├── test_models.py                 # Model unit tests (30+ cases)
├── test_views.py                  # View unit tests (15+ cases)
├── test_forms.py                  # Form unit tests (15+ cases)
├── test_integration.py            # Integration tests (20+ cases)
├── test_ai_and_utils.py           # AI model and utility tests
└── README.md                      # Detailed testing documentation
```

### Test Categories

#### 1. **Model Tests** (test_models.py)
Tests for database models and relationships:
- CustomUser, FarmerProfile, BuyerProfile
- Crop, Order, PurchaseRequest
- ChatRoom, ChatMessage
- WishlistItem, SavedCrop

**Example:**
```python
def test_create_farmer_user(self):
    user = User.objects.create_user(
        username='farmer1',
        role='farmer'
    )
    assert user.role == 'farmer'
```

#### 2. **View Tests** (test_views.py)
HTTP endpoint tests:
- Authentication (login, register)
- Farmer dashboard
- Buyer marketplace
- Admin panel
- Public pages

**Example:**
```python
def test_farmer_dashboard_access(self, farmer_user):
    client = Client()
    client.login(username='testfarmer', password='testpass123')
    response = client.get('/farmer/dashboard/')
    assert response.status_code == 200
```

#### 3. **Form Tests** (test_forms.py)
Form validation and functionality:
- Registration forms
- Crop listing forms
- Purchase request forms

**Example:**
```python
def test_farmer_registration_with_pin(self):
    data = {
        'full_name': 'John Farmer',
        'role': 'farmer',
        'pin': '1234',
        'confirm_pin': '1234'
    }
    form = DynamicRegistrationForm(data)
    assert form.is_valid()
```

#### 4. **Integration Tests** (test_integration.py)
End-to-end workflows:
- User registration and approval
- Crop listing and search
- Purchase request workflow
- Messaging between users
- Order lifecycle

**Example:**
```python
def test_complete_purchase_request_workflow(self, crop, buyer_user):
    # Create purchase request
    pr = PurchaseRequest.objects.create(...)
    assert pr.status == 'pending'
    
    # Farmer accepts
    pr.status = 'accepted'
    pr.save()
    
    # Create order
    order = Order.objects.create(...)
    assert order.status == 'confirmed'
```

#### 5. **AI & Utility Tests** (test_ai_and_utils.py)
AI models and helper functions:
- Price prediction
- Disease detection
- Weather service
- Data validation
- Search utilities

---

## Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestCustomUserModel::test_create_farmer_user
```

### Advanced Options
```bash
# Run with coverage
pytest --cov=. --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Run only fast tests (skip slow)
pytest -m "not slow"

# Run with full output (no capture)
pytest -s

# Run with debugger on failure
pytest --pdb

# Run with timeout (seconds)
pytest --timeout=10
```

### Test Markers
```bash
# Run by type
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only

# Run by feature
pytest -m models           # Model tests
pytest -m views            # View tests
pytest -m forms            # Form tests
```

---

## Test Coverage

### Generate Coverage Reports
```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml
```

### Coverage Goals by Module
| Module | Target | Current |
|--------|--------|---------|
| users | 90% | 85% |
| farmer | 85% | 80% |
| buyer | 85% | 80% |
| chat | 85% | 75% |
| admin_panel | 75% | 70% |
| Overall | 80% | ~75% |

### Improving Coverage
1. Add tests for edge cases
2. Test error conditions
3. Cover form validation
4. Test permission checks
5. Add integration tests

---

## Writing Tests

### Test Structure (Arrange-Act-Assert)
```python
def test_something(self, fixture):
    # Arrange: Set up test data
    user = User.objects.create_user(...)
    
    # Act: Execute the functionality
    result = some_function(user)
    
    # Assert: Verify the result
    assert result.value == expected_value
```

### Using Fixtures
```python
# Fixtures automatically available to all tests
def test_with_fixtures(farmer_user, crop, buyer_user):
    assert crop.farmer == farmer_user
    assert crop.is_available
```

### Testing Models
```python
@pytest.mark.django_db
def test_crop_creation():
    crop = Crop.objects.create(
        quantity=100,
        price_per_unit=50,
        ...
    )
    assert crop.quantity == 100
```

### Testing Views
```python
def test_view_access(farmer_user):
    client = Client()
    client.login(username='testfarmer', password='testpass123')
    
    response = client.get('/farmer/dashboard/')
    assert response.status_code == 200
    assert 'dashboard' in response.context
```

### Testing Forms
```python
def test_form_validation():
    data = {
        'full_name': 'Test',
        'phone_number': '+8801712345678',
        ...
    }
    form = MyForm(data)
    assert form.is_valid()
```

### Testing Workflows
```python
def test_complete_workflow(farmer_user, buyer_user):
    # Step 1: Farmer posts crop
    crop = Crop.objects.create(...)
    
    # Step 2: Buyer views crop
    crops = Crop.objects.filter(is_available=True)
    assert crop in crops
    
    # Step 3: Buyer makes purchase request
    pr = PurchaseRequest.objects.create(...)
    
    # Step 4: Verify workflow completed
    assert pr.status == 'pending'
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt -r docs/requirements-test.txt
      
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### GitLab CI Example
```yaml
test:
  image: python:3.11
  script:
    - pip install -r requirements.txt -r docs/requirements-test.txt
    - pytest --cov=. --cov-report=term --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## Troubleshooting

### Issue: Tests Fail with "Module not found"
**Solution:**
```bash
# Ensure DJANGO_SETTINGS_MODULE is set
export DJANGO_SETTINGS_MODULE=settings

# Or run from correct directory
cd /path/to/AgriGenie
python -m pytest
```

### Issue: Database Lock Errors
**Solution:**
```bash
# Use isolated database per test
pytest --nomigrations --db=sequential
```

### Issue: Tests Are Too Slow
**Solution:**
```bash
# Run in parallel
pip install pytest-xdist
pytest -n auto

# Use transactions for speed
@pytest.mark.django_db(transaction=True)
def test_something():
    pass
```

### Issue: Fixture Not Found
**Solution:**
```bash
# Ensure conftest.py is in tests/ directory
# Or import fixtures explicitly
from tests.conftest import farmer_user
```

### Issue: Tests Pass Locally, Fail in CI
**Solution:**
```bash
# Ensure consistent environment
pip freeze > requirements.lock
python -m pytest --tb=long  # Full traceback
```

### Debugging Tests
```bash
# Print debug output
pytest -s

# Stop on first failure
pytest -x

# Run failed tests only
pytest --lf

# Drop into debugger on failure
pytest --pdb

# Verbose output
pytest -vv
```

---

## Best Practices

✅ **DO:**
- Write meaningful test names
- Use fixtures to reduce duplication
- Test one thing per test
- Keep tests fast
- Test edge cases
- Use assertions clearly
- Document complex tests

❌ **DON'T:**
- Skip test execution
- Have interdependent tests
- Test multiple features in one test
- Use hardcoded data
- Ignore warnings
- Make HTTP requests in unit tests
- Leave debugging code

---

## Next Steps

1. **Run full test suite**: `pytest`
2. **View coverage**: `pytest --cov=. --cov-report=html && open htmlcov/index.html`
3. **Add new tests**: Create test cases for new features
4. **Monitor coverage**: Aim for >80% coverage
5. **Integrate with CI/CD**: Add test automation to pipeline

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Pytest-Django](https://pytest-django.readthedocs.io/)
- [Test Best Practices](https://testing-library.com/docs/queries/about/#priority)

---

**Last Updated**: April 2026
**Version**: 1.0
**Maintained by**: AgriGenie Development Team
