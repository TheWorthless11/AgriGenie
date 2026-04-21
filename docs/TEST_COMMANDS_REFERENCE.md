# Test Commands Reference Card

## 🚀 Essential Commands

### Installation
```bash
# Install testing dependencies
pip install -r docs/requirements-test.txt
```

### Basic Execution
```bash
# Run all tests
pytest

# Run with output
pytest -v

# Show prints (debugging)
pytest -s

# Stop on first failure
pytest -x
```

---

## 📑 Run by File

```bash
# All model tests
pytest tests/test_models.py

# All view tests
pytest tests/test_views.py

# All form tests
pytest tests/test_forms.py

# All integration tests
pytest tests/test_integration.py

# All AI/utility tests
pytest tests/test_ai_and_utils.py
```

---

## 🎯 Run by Category

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Slow tests only
pytest -m slow

# Skip slow tests
pytest -m "not slow"

# Multiple markers
pytest -m "unit or integration"
```

---

## 🔍 Run Specific Tests

```bash
# Run single test file
pytest tests/test_models.py

# Run single test class
pytest tests/test_models.py::TestCustomUserModel

# Run single test method
pytest tests/test_models.py::TestCustomUserModel::test_create_farmer

# Multiple specific tests
pytest tests/test_models.py::Test1::method1 tests/test_forms.py::Test2::method2
```

---

## 📊 Coverage Commands

```bash
# Terminal coverage report
pytest --cov=.

# Coverage with missing lines
pytest --cov=. --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=. --cov-report=html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac/Linux

# Multiple format reports
pytest --cov=. --cov-report=term-missing --cov-report=html --cov-report=json

# Coverage of specific module
pytest --cov=farmer --cov=buyer --cov=chat
```

---

## ⚡ Performance Commands

```bash
# Run in parallel (faster)
pytest -n auto

# Show slowest 10 tests
pytest --durations=10

# Show slowest 5 tests
pytest --durations=5

# Quiet mode (less output)
pytest -q

# Very verbose
pytest -vv
```

---

## 🔧 Debug Commands

```bash
# Drop to debugger on failure
pytest --pdb

# Continue debugging on other failures
pytest -x --pdb

# Show print statements
pytest -s

# Full output (no capture)
pytest -vv -s

# Show local variables on failure
pytest -l

# Full traceback
pytest --tb=long

# Short traceback
pytest --tb=short

# No traceback
pytest --tb=no
```

---

## 🔄 Re-running Commands

```bash
# Run only failed tests from last run
pytest --lf

# Run failed tests first, then others
pytest --ff

# Run last N failed tests
pytest --lastfailed=2
```

---

## 🔐 Isolation Commands

```bash
# Run test in isolation (no DB)
pytest --no-db

# Use sequential database access
pytest --db=sequential

# Create fresh test database
pytest --create-db

# Keep test database after run
pytest --keep-db

# Reuse test database (faster)
pytest --reuse-db
```

---

## 📋 Reporting Commands

```bash
# JSON report
pytest --json=report.json

# JUnit XML report (CI/CD)
pytest --junit-xml=report.xml

# Summary report
pytest -ra

# Show each test result
pytest -v

# Quiet summary
pytest -q --tb=no
```

---

## 🎨 Output Formatting

```bash
# Verbose with coverage
pytest -v --cov=. --cov-report=term-missing

# Minimal output
pytest -q

# Pretty colors
pytest --color=yes

# No colors (CI servers)
pytest --color=no

# Show assertion details
pytest -vv

# Pretty assertion diffs
pytest --tb=short -vv
```

---

## 🚫 Skip & Filter Commands

```bash
# Skip slow tests
pytest -m "not slow"

# Skip integration tests
pytest -m "not integration"

# Run only slow tests
pytest -m slow

# Skip by keyword
pytest --deselect tests/test_models.py::TestCrop::test_slow

# Skip patterns
pytest --ignore=tests/test_integration.py
```

---

## 🔗 Combined Commands (Most Useful)

```bash
# Development workflow (fast feedback)
pytest -x -v

# Commit workflow (comprehensive)
pytest -v --cov=. --cov-report=term-missing

# CI/CD pipeline
pytest --cov=. --cov-report=xml --junit-xml=report.xml -v

# Debug failing test
pytest tests/test_models.py::TestModel::test_case -vv -s --pdb

# Performance analysis
pytest --durations=10 -v

# Full validation before push
pytest -v --cov=. --cov-report=term-missing && echo "✅ All checks passed!"

# Fast iteration during development
pytest tests/test_models.py -x -v -s
```

---

## 🔤 Common Aliases (Add to .bashrc/.zshrc)

```bash
# Add to shell config file
alias pytest-quick='pytest -x -v'
alias pytest-verbose='pytest -vv -s'
alias pytest-coverage='pytest --cov=. --cov-report=html && open htmlcov/index.html'
alias pytest-debug='pytest --pdb -s'
alias pytest-failed='pytest --lf -v'
alias pytest-slow='pytest --durations=10'
```

---

## 🆚 Environment Variables

```bash
# Set Django settings
export DJANGO_SETTINGS_MODULE=settings

# Disable migrations (faster)
export PYTEST_DJANGO_FIND_PROJECT=false

# Timeout per test (seconds)
export PYTEST_TIMEOUT=300

# Minimum coverage percentage
export COVERAGE_MIN_PERCENTAGE=80

# Custom pytest args
export PYTEST_ADDOPTS="-n auto -v"
```

---

## 📱 Command Patterns for Different Scenarios

### 🏃 Quick Development Loop (1-2 seconds)
```bash
pytest tests/test_models.py::TestCrop -x -v
```

### 🔍 Debugging a Failure
```bash
pytest tests/test_models.py::TestCrop::test_specific -vv -s --pdb
```

### ✅ Before Committing Code
```bash
pytest -v --cov=. --cov-report=term-missing --no-cov-on-fail
```

### 🚀 CI/CD Pipeline
```bash
pytest --cov=. --cov-report=xml --junit-xml=report.xml -v --tb=short
```

### 📊 Coverage Analysis
```bash
pytest --cov=. --cov-report=html --cov-report=term-missing && open htmlcov/index.html
```

### 🔄 Re-running Failed Tests
```bash
pytest --lf -v -x
```

### ⚡ Performance Testing
```bash
pytest --durations=10 -v --co | head -20
```

### 🎯 Running Test Suite by Component
```bash
# Run all farmer app tests
pytest tests/test_models.py -k "Farmer" -v

# Run all authentication tests
pytest tests/test_views.py -k "auth" -v

# Run all form validation tests
pytest tests/test_forms.py -k "validation" -v
```

---

## 💡 Pro Tips

### 1. Create Custom Test Commands in setup.cfg
```ini
[tool:pytest]
addopts = -ra --strict-markers -v
testpaths = tests
```

### 2. Use Test Markers for Organization
```python
@pytest.mark.slow
@pytest.mark.integration
def test_something():
    pass
```

### 3. Watch Tests for Development
```bash
# Install pytest-watch
pip install pytest-watch

# Watch and re-run on file change
ptw tests/
```

### 4. Parallel Execution for Speed
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 cores
pytest -n 4
```

### 5. Test Code Coverage Target
```bash
# Fail if coverage drops below 80%
pytest --cov=. --cov-fail-under=80
```

---

## 🔗 Quick Links

- [Full Testing Guide](TESTING_GUIDE.md)
- [Quick Start Guide](TESTING_QUICKSTART.md)
- [Framework Architecture](TEST_FRAMEWORK_ARCHITECTURE.md)
- [Pytest Docs](https://docs.pytest.org/)
- [Django Testing Docs](https://docs.djangoproject.com/en/4.2/topics/testing/)

---

## 📌 Bookmark This!

Print or bookmark this page for quick reference while developing.

**Last Updated**: April 2026
**For AgriGenie Development Team**
