"""
Tests for core API endpoints
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import pandas as pd


class TestAuthEndpoints:
    """Tests for authentication endpoints"""
    
    @patch('main.authenticate_user')
    def test_login_success(self, mock_auth, client):
        """Test successful login"""
        mock_auth.return_value = {
            "access_token": "test.token.here",
            "email": "user@company.com",
            "name": "Test User",
            "region": "R06 JABODEBEK",
            "role": "viewer",
            "permissions": ["dashboard.view"]
        }
        
        response = client.post("/api/auth/login", json={
            "email": "user@company.com",
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    @patch('main.authenticate_user')
    def test_login_invalid_credentials(self, mock_auth, client):
        """Test login with invalid credentials"""
        mock_auth.return_value = None
        
        response = client.post("/api/auth/login", json={
            "email": "wrong@company.com",
            "password": "wrongpass"
        })
        
        assert response.status_code == 401
    
    @patch('main.get_current_user')
    def test_get_me_success(self, mock_get_user, client, mock_user_region_a, auth_headers):
        """Test getting current user info"""
        mock_get_user.return_value = mock_user_region_a
        
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == mock_user_region_a["email"]
        assert data["region"] == mock_user_region_a["region"]


class TestDashboardEndpoints:
    """Tests for dashboard endpoints"""
    
    @patch('main.get_user_region')
    @patch('main.data_generator')
    def test_get_sales_data(self, mock_data_gen, mock_region, client, auth_headers):
        """Test getting sales data"""
        mock_region.return_value = "R06 JABODEBEK"
        
        # Mock DataFrame
        mock_df = pd.DataFrame([
            {"week": "2024-W01", "revenue": 100000},
            {"week": "2024-W02", "revenue": 120000}
        ])
        mock_data_gen.get_sales_data.return_value = mock_df
        
        response = client.get("/api/dashboard/sales", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    @patch('main.get_user_region')
    @patch('main.cache_manager')
    def test_get_kpis(self, mock_cache, mock_region, client, auth_headers):
        """Test getting KPIs"""
        mock_region.return_value = "R06 JABODEBEK"
        mock_cache.get_kpis_cached.return_value = {
            "total_revenue": 1000000,
            "total_target": 1200000,
            "achievement_rate": 83.33,
            "growth_rate": 10.5,
            "next_month_forecast": 1100000
        }
        
        response = client.get("/api/dashboard/kpis", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "achievement_rate" in data
    
    @patch('main.get_user_region')
    @patch('main.data_generator')
    def test_get_targets(self, mock_data_gen, mock_region, client, auth_headers):
        """Test getting target data"""
        mock_region.return_value = "R06 JABODEBEK"
        
        mock_df = pd.DataFrame([
            {"month": "2024-01", "target": 1000000, "actual": 950000}
        ])
        mock_data_gen.get_target_data.return_value = mock_df
        
        response = client.get("/api/dashboard/targets", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestLeaderboardEndpoints:
    """Tests for leaderboard endpoints"""
    
    @patch('main.get_user_region')
    @patch('main.cache_manager')
    def test_get_leaderboard(self, mock_cache, mock_region, client, auth_headers):
        """Test getting leaderboard"""
        mock_region.return_value = "R06 JABODEBEK"
        mock_cache.get_leaderboard.return_value = [
            {"rank": 1, "name": "Salesman A", "revenue": 500000},
            {"rank": 2, "name": "Salesman B", "revenue": 450000}
        ]
        
        response = client.get("/api/leaderboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    @patch('main.get_user_region')
    @patch('main.cache_manager')
    def test_get_leaderboard_with_limit(self, mock_cache, mock_region, client, auth_headers):
        """Test leaderboard with limit parameter"""
        mock_region.return_value = "R06 JABODEBEK"
        mock_cache.get_leaderboard.return_value = [
            {"rank": 1, "name": "Salesman A", "revenue": 500000}
        ]
        
        response = client.get("/api/leaderboard?limit=1", headers=auth_headers)
        
        assert response.status_code == 200
        mock_cache.get_leaderboard.assert_called_once()
    
    @patch('main.get_current_user')
    @patch('main.cache_manager')
    def test_get_leaderboard_admin_override_region(self, mock_cache, mock_get_user, client, admin_headers, mock_user_admin):
        """Test admin can override region filter"""
        mock_get_user.return_value = mock_user_admin
        mock_cache.get_leaderboard.return_value = []
        
        response = client.get("/api/leaderboard?region=R07 BANDUNG", headers=admin_headers)
        
        assert response.status_code == 200
        # Verify cache was called with overridden region
        call_args = mock_cache.get_leaderboard.call_args
        assert call_args[1]["region"] == "R07 BANDUNG"


class TestRLSEnforcement:
    """Tests for Row-Level Security enforcement"""
    
    @patch('main.get_user_region')
    @patch('main.data_generator')
    def test_rls_filters_by_region(self, mock_data_gen, mock_region, client, auth_headers):
        """Test that data is filtered by user region"""
        mock_region.return_value = "R06 JABODEBEK"
        
        mock_df = pd.DataFrame([
            {"region": "R06 JABODEBEK", "revenue": 100000}
        ])
        mock_data_gen.get_sales_data.return_value = mock_df
        
        response = client.get("/api/dashboard/sales", headers=auth_headers)
        
        assert response.status_code == 200
        # Verify get_sales_data was called with correct region
        mock_data_gen.get_sales_data.assert_called_once_with("R06 JABODEBEK")
    
    @patch('main.get_current_user')
    @patch('main.data_generator')
    def test_admin_sees_all_regions(self, mock_data_gen, mock_get_user, client, admin_headers, mock_user_admin):
        """Test that admin users can access all regions"""
        mock_get_user.return_value = mock_user_admin
        mock_data_gen.get_region_comparison.return_value = []
        
        response = client.get("/api/dashboard/region-comparison", headers=admin_headers)
        
        assert response.status_code == 200
    
    @patch('main.get_current_user')
    @patch('main.data_generator')
    def test_regular_user_cannot_access_region_comparison(self, mock_data_gen, mock_get_user, client, auth_headers, mock_user_region_a):
        """Test that regular users cannot access region comparison"""
        mock_get_user.return_value = mock_user_region_a
        
        response = client.get("/api/dashboard/region-comparison", headers=auth_headers)
        
        assert response.status_code == 403


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check_no_auth(self, client):
        """Test health endpoint doesn't require authentication"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
