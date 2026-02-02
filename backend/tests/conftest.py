"""
Pytest configuration and shared fixtures
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any
import os

# Set test environment variables before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["BIGQUERY_PROJECT_ID"] = "test-project"
os.environ["BIGQUERY_DATASET"] = "test-dataset"
os.environ["BIGQUERY_TABLE"] = "test-table"

from main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_user_region_a():
    """Mock user with Region A access"""
    return {
        "email": "user-a@company.com",
        "name": "User A",
        "region": "R06 JABODEBEK",
        "role": "viewer",
        "permissions": ["dashboard.view"],
        "nik": "NIK001",
        "scope": "REGION",
        "scope_id": "R06 JABODEBEK"
    }


@pytest.fixture
def mock_user_admin():
    """Mock admin user with ALL region access"""
    return {
        "email": "admin@company.com",
        "name": "Admin User",
        "region": "ALL",
        "role": "super_admin",
        "permissions": ["*"],  # All permissions
        "nik": "ADMIN001",
        "scope": "NATIONAL",
        "scope_id": None
    }


@pytest.fixture
def mock_user_viewer():
    """Mock viewer user"""
    return {
        "email": "viewer@company.com",
        "name": "Viewer User",
        "region": "R07 BANDUNG",
        "role": "viewer",
        "permissions": ["dashboard.view"],
        "nik": "VIEW001",
        "scope": "REGION",
        "scope_id": "R07 BANDUNG"
    }


@pytest.fixture
def mock_token():
    """Mock JWT token"""
    return "mock.jwt.token.here"


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase API response"""
    return {
        "data": [],
        "status": 200
    }


@pytest.fixture
def mock_bigquery_service():
    """Mock BigQuery service"""
    mock_service = Mock()
    mock_service.project_id = "test-project"
    mock_service.dataset = "test-dataset"
    mock_service.table = "test-table"
    mock_service.full_table_id = "`test-project.test-dataset.test-table`"
    
    # Mock methods
    mock_service.get_cutoff_date.return_value = "2024-01-01"
    mock_service.get_leaderboard.return_value = Mock()  # Will be DataFrame in real tests
    mock_service.get_kpis.return_value = {
        "total_revenue": 1000000,
        "total_target": 1200000,
        "achievement_rate": 83.33,
        "growth_rate": 10.5,
        "next_month_forecast": 1100000
    }
    
    return mock_service


@pytest.fixture
def mock_data_generator():
    """Mock data generator"""
    mock_gen = Mock()
    mock_gen.get_sales_data.return_value = Mock()  # DataFrame
    mock_gen.get_target_data.return_value = Mock()  # DataFrame
    mock_gen.get_forecast_data.return_value = Mock()  # DataFrame
    mock_gen.get_top_products.return_value = []
    mock_gen.get_region_comparison.return_value = []
    
    return mock_gen


@pytest.fixture
def auth_headers(mock_token):
    """Create authorization headers with mock token"""
    return {"Authorization": f"Bearer {mock_token}"}


@pytest.fixture
def admin_headers(mock_token):
    """Create authorization headers for admin"""
    return {"Authorization": f"Bearer {mock_token}"}


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset cache before each test"""
    # Clear RBAC cache
    from rbac import ROLE_PERMISSIONS_CACHE
    ROLE_PERMISSIONS_CACHE.clear()
    yield
    ROLE_PERMISSIONS_CACHE.clear()
