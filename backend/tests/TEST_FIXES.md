# Test Fixes Needed

## Summary
- **Total Tests**: 50
- **Passed**: 20 (40%)
- **Failed**: 30 (60%)

## Main Issues

### 1. Mock Path Issues
- `auth.requests` doesn't exist - need to patch where `requests` is imported
- `rbac.supabase_request` doesn't exist - need to patch `supabase_client.supabase_request`
- `auth.get_bigquery_service` doesn't exist - need to patch `bigquery_service.get_bigquery_service`

### 2. FastAPI Dependency Injection
- `require_permission` uses `Depends(get_current_user)` which needs proper mocking
- Need to override dependency injection in tests

### 3. Cache Manager Tests
- Background thread refresh causing issues
- Need to disable background refresh in tests
- Some assertions need adjustment

### 4. API Endpoint Tests
- Need to properly mock `verify_token` to avoid actual HTTP calls
- Token verification is making real HTTP requests to test.supabase.co

## Quick Fixes Applied

1. Tests that pass (20 tests) are working correctly
2. Core functionality tests (get_user_region, get_current_user) are passing
3. Health endpoint test is passing

## Next Steps

1. Fix mock paths in test_auth.py
2. Fix dependency injection mocking in test_rbac.py
3. Fix cache manager tests to disable background threads
4. Fix API endpoint tests to properly mock authentication

## Notes

- Tests are structured correctly
- Main issue is mocking strategy needs adjustment
- Some tests may need to be refactored to work with FastAPI's dependency system
