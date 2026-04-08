# AgriGenie Testing Documentation

## Overview

This document provides comprehensive guidance on running unit tests, integration tests, and the entire test suite for the AgriGenie project.

## Test Structure

```
tests/
├── __init__.py                 # Tests package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_models.py              # Unit tests for all models
├── test_views.py               # Unit tests for views (HTTP endpoints)
├── test_forms.py               # Unit tests for forms
├── test_integration.py         # Integration tests for complete workflows
└── README.md                   # This file
```

## Test Categories

### 1. **Unit Tests** (`test_models.py`, `test_views.py`, `test_forms.py`)
- Test individual components in isolation
- Cover model creation, validation, and relationships
- Test form validation and error handling
- Verify view access control and responses
- **Files:**
  - `test_models.py`: CustomUser, FarmerProfile, BuyerProfile, Crop, Order, Chat, etc.
  - `test_views.py`: Authentication, farmer dashboard, buyer marketplace, admin panel
  - `test_forms.py`: Registration, crop creation, purchase requests

### 2. **Integration Tests** (`test_integration.py`)
- Test complete user workflows and journeys
- Verify interactions between multiple components
- Cover end-to-end scenarios like:
  - User registration → profile approval → crop posting
  - Crop listing → purchase request → order → delivery
  - Real-time messaging workflows

## Prerequisites

Install testing dependencies:

```bash
pip install pytest==7.4.3
pip install pytest-django==4.7.0
pip install pytest-cov==4.1.0
pip install model-bakery==1.12.0
```

Or use the dev requirements:

```bash
pip install -r docs/requirements-dev.txt
```

## Running Tests

### 1. **Run All Tests**
```bash
pytest
```

### 2. **Run Specific Test File**
```bash
# Unit tests for models only
pytest tests/test_models.py

# Unit tests for views only
pytest tests/test_views.py

# Integration tests only
pytest tests/test_integration.py
```

### 3. **Run Specific Test Class**
```bash
pytest tests/test_models.py::TestCustomUserModel
pytest tests/test_integration.py::TestCropListingAndSearchWorkflow
```

### 4. **Run Specific Test Method**
```bash
pytest tests/test_models.py::TestCustomUserModel::test_create_farmer_user
pytest tests/test_integration.py::TestPurchaseWorkflow::test_complete_purchase_request_workflow
```

### 5. **Run with Coverage Report**
```bash
pytest --cov=. --cov-report=html
```
This generates an HTML coverage report in `htmlcov/index.html`

### 6. **Run with Verbose Output**
```bash
pytest -v
```

### 7. **Run Only Fast Tests** (exclude slow tests)
```bash
pytest -m "not slow"
```

### 8. **Run Only Unit Tests**
```bash
pytest -m unit
```

### 9. **Run Only Integration Tests**
```bash
pytest -m integration
```

### 10. **Run Tests by Marker**
```bash
# Model tests
pytest -m models

# View tests
pytest -m views

# Form tests
pytest -m forms
```

### 11. **Run with Different Output Formats**
```bash
# JUnit XML (for CI/CD)
pytest --junit-xml=test-results.xml

# TAP format
pytest --tap-stream

# Full test output
pytest --capture=no
```

### 12. **Run Tests in Parallel** (faster execution)
```bash
pip install pytest-xdist
pytest -n auto  # Uses all CPU cores
```

## Test Fixtures

Pytest fixtures are defined in `conftest.py` and automatically available to all tests:

```python
# Available fixtures:
- farmer_user          # Test farmer user with PIN auth
- farmer_profile       # Farmer profile with farm details
- buyer_user           # Test buyer user
- buyer_profile        # Buyer profile with company details
- master_crop          # Master crop template (e.g., Tomato)
- crop                 # Active crop listing by farmer
- admin_user           # Superuser/admin account
```

### Using Fixtures in Tests

```python
def test_with_fixtures(farmer_user, crop, buyer_user):
    """Fixtures are automatically injected"""
    assert crop.farmer == farmer_user
    assert crop.is_available
```

## Test Coverage

View coverage reports:

```bash
# Generate coverage report
pytest --cov=. --cov-report=term-missing --cov-report=html

# Open HTML report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

## Database for Tests

- Tests use a temporary SQLite database
- Database is created fresh for each test run
- Database is automatically cleaned up after tests complete
- No manual database setup needed

## Writing New Tests

### Unit Test Example
```python
import pytest

pytestmark = pytest.mark.django_db

class TestMyFeature:
    def test_something(self, farmer_user):
        """Test description"""
        assert farmer_user.role == 'farmer'
```

### Integration Test Example
```python
def test_workflow(farmer_user, buyer_user, crop):
    """Test complete workflow"""
    # Step 1: Setup
    # Step 2: Execute
    # Step 3: Assert
    assert crop.farmer == farmer_user
```

## Continuous Integration

For CI/CD pipelines (GitHub Actions, GitLab CI, etc.):

```bash
# Run tests with coverage and generate reports
pytest --cov=. --cov-report=xml --junit-xml=test-results.xml -v
```

## Common Issues & Solutions

### Issue: Tests are slow
**Solution:**
```bash
# Run in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"
```

### Issue: Database lock errors
**Solution:**
```bash
# Use in-memory database
pytest --nomigrations
```

### Issue: Module not found errors
**Solution:**
```bash
# Ensure you're in correct directory
cd path/to/AgriGenie

# Ensure Django settings are configured
export DJANGO_SETTINGS_MODULE=settings
```

### Issue: Import errors in tests
**Solution:**
```bash
# Ensure tests directory is in Python path
python -m pytest tests/
```

## Test Statistics

Current test suite coverage:

- **Model Tests**: 30+ test cases
  - User models: 7 tests
  - Profile models: 4 tests
  - Crop models: 10+ tests
  - Chat models: 5 tests
  - Other models: 4+ tests

- **View Tests**: 15+ test cases
  - Authentication views: 2 tests
  - Farmer dashboard: 2 tests
  - Buyer dashboard: 2 tests
  - Admin panel: 2 tests
  - Public pages: 3 tests
  - API routes: 3 tests

- **Form Tests**: 15+ test cases
  - Registration forms: 5 tests
  - Crop forms: 5 tests
  - Purchase request forms: 3 tests
  - Form validation: 2 tests

- **Integration Tests**: 20+ test cases
  - User registration workflows: 2 tests
  - Crop listing workflows: 2 tests
  - Purchase workflows: 3 tests
  - Wishlist workflows: 2 tests
  - Messaging workflows: 2 tests
  - Order lifecycle: 2 tests
  - Availability workflows: 2 tests

**Total: 80+ test cases**

## Best Practices

1. **Use Fixtures**: Leverage pytest fixtures to reduce code duplication
2. **Clear Test Names**: Use descriptive names like `test_farmer_cannot_access_buyer_dashboard`
3. **One Thing Per Test**: Each test should verify one behavior
4. **Arrange-Act-Assert**: Structure tests with setup, execution, and assertions
5. **Test Edge Cases**: Include tests for invalid inputs and error conditions
6. **Mock External Services**: Mock email, SMS, file uploads in tests
7. **Use Markers**: Tag tests with `@pytest.mark.slow` for slow tests

## Debugging Failed Tests

### Run with Full Traceback
```bash
pytest -vv --tb=long test_file.py
```

### Use Python Debugger
```bash
pytest --pdb tests/test_models.py::TestCustomUserModel::test_create_farmer_user
```

### Print Debug Info
```python
def test_with_debug_output(farmer_user):
    print(f"User: {farmer_user}")
    print(f"Role: {farmer_user.role}")
    assert True
```

Run with:
```bash
pytest -s  # Shows print output
```

## Performance Optimization

### 1. Use Database Transactions
```python
@pytest.mark.django_db
def test_something():
    # Automatic transaction rollback after test
    pass
```

### 2. Use Fixture Caching
```python
@pytest.fixture(scope="session")
def master_crop():
    # Created once per test session
    pass
```

### 3. Run Tests in Parallel
```bash
pytest -n auto
```

## Contributing Tests

When adding new features:

1. Write tests FIRST (TDD) or immediately after implementation
2. Ensure tests pass before committing
3. Maintain >80% code coverage
4. Document complex test scenarios
5. Follow existing test patterns and fixtures

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing Documentation](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Pytest-Django Documentation](https://pytest-django.readthedocs.io/)

---

**Last Updated**: April 2026
**Maintainer**: AgriGenie Development Team
