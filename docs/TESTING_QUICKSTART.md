# Testing Quick Start Guide

## 🚀 Get Started in 2 Minutes

### Step 1: Install Testing Dependencies
```bash
# Navigate to project directory
cd c:\Users\Shaila\.vscode\AgriGenie\AgriGenie

# Install all testing packages
pip install -r docs/requirements-test.txt
```

**What gets installed:**
- pytest, pytest-django, pytest-cov
- model-bakery, faker (test data generation)
- black, flake8, isort (code quality)
- ipython, ipdb (debugging)

---

### Step 2: Run All Tests
```bash
# Simple run - shows pass/fail for each test
pytest

# Verbose - shows each test case
pytest -v

# Show print statements (good for debugging)
pytest -s

# Stop on first failure
pytest -x
```

**Expected Output:**
```
tests/test_models.py ......................    [30%]
tests/test_views.py ...............              [45%]
tests/test_forms.py ..................         [60%]
tests/test_integration.py ...........          [75%]
tests/test_ai_and_utils.py ...........         [100%]

======================== 80+ passed in 5.23s ========================
```

---

### Step 3: Check Test Coverage
```bash
# Generate coverage report (terminal)
pytest --cov=. --cov-report=term-missing

# Generate HTML report (opens in browser)
pytest --cov=. --cov-report=html
start htmlcov/index.html
```

**Coverage checks:**
- Missing lines shown with line numbers
- HTML report shows visual coverage by file
- Target: Aim for >80% coverage

---

## 🎯 Common Commands Cheat Sheet

### Run Specific Tests
```bash
# Run only model tests
pytest tests/test_models.py

# Run only farmer-related tests
pytest tests/test_models.py::TestFarmerProfile

# Run specific test
pytest tests/test_models.py::TestCustomUserModel::test_create_farmer_user

# Run by marker
pytest -m unit          # unit tests only
pytest -m integration   # integration tests only
```

### Run Tests Faster
```bash
# Run in parallel (requires: pip install pytest-xdist)
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Run failed, then all
pytest --ff
```

### Debug Tests
```bash
# Drop into debugger on failure
pytest --pdb

# Show full output (don't capture prints)
pytest -s

# Extra verbose (shows full assertion diffs)
pytest -vv

# Show slowest tests
pytest --durations=10
```

### Generate Reports
```bash
# Terminal coverage with missing lines
pytest --cov=. --cov-report=term-missing

# HTML coverage report
pytest --cov=. --cov-report=html

# JSON report (for automation)
pytest --cov=. --cov-report=json

# Combine all reports
pytest --cov=. --cov-report=term --cov-report=html --cov-report=json
```

---

## ✅ Quick Verification Checklist

Run this after installing dependencies to verify everything works:

```bash
# 1. Check pytest is installed correctly
pytest --version
# Expected: pytest version 7.4.3 or higher

# 2. Run minimal test
pytest tests/test_models.py::TestCustomUserModel::test_create_farmer_user -v

# 3. Run all tests (should pass)
pytest -v

# 4. Check coverage
pytest --cov=. --cov-report=term-missing

# 5. Verify HTML report generation
pytest --cov=. --cov-report=html
```

---

## 📊 Test Summary

| Test Module | Test Count | Coverage |
|-------------|-----------|----------|
| test_models.py | 35+ | Models, relationships, validation |
| test_views.py | 20+ | HTTP endpoints, access control |
| test_forms.py | 15+ | Form validation, error handling |
| test_integration.py | 20+ | Complete workflows |
| test_ai_and_utils.py | 10+ | AI models, utilities |
| **TOTAL** | **100+** | **~75%** |

---

## 🔧 Troubleshooting Table

| Problem | Solution |
|---------|----------|
| **pytest: command not found** | Run: `pip install -r docs/requirements-test.txt` |
| **ModuleNotFoundError: No module named 'tests'** | Run tests from project root: `cd AgriGenie && pytest` |
| **FAILED - database read-only** | Ensure db.sqlite3 permissions allow writing |
| **Tests timeout** | Run: `pytest --timeout=60` |
| **Memory errors** | Run sequentially: `pytest -n 1` |
| **Import errors** | Ensure PYTHONPATH includes project: `export PYTHONPATH=.` |

---

## 🎓 Next Steps

### After First Run:
1. ✅ Verify all tests pass
2. ✅ Check coverage report (target: >80%)
3. ✅ Commit test files to git:
   ```bash
   git add tests/ docs/requirements-test.txt pytest.ini setup.cfg
   git commit -m "test: Add comprehensive test suite with 100+ test cases"
   git push origin main
   ```

### For New Features:
1. Create feature branch
2. Add tests first (TDD)
3. Implement feature
4. Run tests to verify
5. Push and create PR

### For Code Changes:
```bash
# Before pushing:
pytest -v --cov=.

# Fix any failures
# Then push
```

---

## 📚 Full Documentation

For detailed testing information, see:
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete testing reference
- [tests/README.md](../tests/README.md) - Test structure documentation
- [pytest documentation](https://docs.pytest.org/) - Official docs

---

## ⚡ Quick Commands Reference

```bash
# One-liner to run everything
pytest -v --cov=. --cov-report=html && echo "✅ Tests complete! Open htmlcov/index.html to view coverage"

# Install + run full suite
pip install -r docs/requirements-test.txt && pytest -v --cov=.

# Run and stop on first failure (fail-fast)
pytest -x

# Run with detailed output
pytest -vv -s --tb=long
```

---

**Ready to test?** Start with:
```bash
pip install -r docs/requirements-test.txt
pytest -v
```

Let us know if you encounter any issues! 🚀
