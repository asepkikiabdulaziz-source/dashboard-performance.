# Test Suite Documentation

## Overview

This directory contains the test suite for the Dashboard Performance API. Tests are organized by module and functionality.

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test
```bash
pytest tests/test_auth.py::TestAuthenticateUser::test_authenticate_user_success
```

## Test Structure

```
tests/
├── __init__.py           # Test package initialization
├── conftest.py          # Shared fixtures and configuration
├── test_auth.py         # Authentication tests
├── test_rbac.py         # RBAC tests
├── test_api_endpoints.py # API endpoint tests
└── fixtures/            # Test data fixtures
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)
- User authentication
- Token verification
- User context resolution
- Region extraction

### 2. RBAC Tests (`test_rbac.py`)
- Permission checking
- Role-based access
- Cache functionality
- Super admin bypass

### 3. API Endpoint Tests (`test_api_endpoints.py`)
- Authentication endpoints
- Dashboard endpoints
- Leaderboard endpoints
- RLS enforcement
- Health checks

## Fixtures

Common fixtures are defined in `conftest.py`:

- `client`: FastAPI test client
- `mock_user_region_a`: Mock user with Region A access
- `mock_user_admin`: Mock admin user
- `mock_user_viewer`: Mock viewer user
- `mock_token`: Mock JWT token
- `mock_bigquery_service`: Mock BigQuery service
- `mock_data_generator`: Mock data generator
- `auth_headers`: Authorization headers

## Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import patch

class TestMyFeature:
    """Tests for my feature"""
    
    @patch('module.function')
    def test_feature_success(self, mock_function):
        """Test successful feature execution"""
        mock_function.return_value = {"result": "success"}
        
        # Your test code here
        assert True
```

### Best Practices

1. **Use descriptive test names**: Test names should clearly describe what is being tested
2. **One assertion per test**: Focus each test on a single behavior
3. **Use fixtures**: Reuse common setup code via fixtures
4. **Mock external dependencies**: Mock database calls, API calls, etc.
5. **Test edge cases**: Include tests for error conditions and edge cases
6. **Keep tests fast**: Tests should run quickly, avoid real I/O when possible

## Coverage Goals

- **Critical paths**: 80%+ coverage
- **Core modules**: 70%+ coverage
- **Overall**: 60%+ coverage

## Continuous Integration

Tests should be run automatically in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    cd backend
    pytest --cov=. --cov-report=xml
```

## Troubleshooting

### Import Errors
If you encounter import errors, ensure you're running tests from the backend directory:
```bash
cd backend
pytest
```

### Mock Issues
If mocks aren't working, check that you're patching the correct import path:
```python
# Patch where it's used, not where it's defined
@patch('main.authenticate_user')  # Correct
# NOT: @patch('auth.authenticate_user')  # Wrong if imported in main
```

### Environment Variables
Test environment variables are set in `conftest.py`. Override if needed:
```python
@pytest.fixture
def custom_env(monkeypatch):
    monkeypatch.setenv("CUSTOM_VAR", "value")
```
