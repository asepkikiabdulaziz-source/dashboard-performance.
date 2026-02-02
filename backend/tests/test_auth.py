"""
Tests for authentication module (auth.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from auth import (
    authenticate_user,
    verify_token,
    get_user_region,
    get_current_user,
    resolve_user_slot_context
)


class TestAuthenticateUser:
    """Tests for authenticate_user function"""
    
    @patch('auth.requests.post')
    @patch('auth.resolve_user_slot_context')
    def test_authenticate_user_success(self, mock_resolve, mock_post):
        """Test successful user authentication"""
        # Mock Supabase response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test.token.here",
            "user": {
                "email": "user@company.com",
                "user_metadata": {
                    "name": "Test User",
                    "region": "R06 JABODEBEK",
                    "role": "viewer"
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Mock slot context resolution
        mock_resolve.return_value = {
            "name": "Test User",
            "region": "R06 JABODEBEK",
            "role": "viewer",
            "nik": "NIK001"
        }
        
        result = authenticate_user("user@company.com", "password123")
        
        assert result is not None
        assert result["access_token"] == "test.token.here"
        assert result["email"] == "user@company.com"
        assert result["region"] == "R06 JABODEBEK"
        assert result["role"] == "viewer"
    
    @patch('auth.requests.post')
    def test_authenticate_user_invalid_credentials(self, mock_post):
        """Test authentication with invalid credentials"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = authenticate_user("wrong@company.com", "wrongpass")
        
        assert result is None
    
    @patch('auth.requests.post')
    def test_authenticate_user_missing_env_vars(self, mock_post):
        """Test authentication when Supabase URL/Key is missing"""
        import os
        original_url = os.environ.get("SUPABASE_URL")
        original_key = os.environ.get("SUPABASE_KEY")
        
        try:
            # Remove env vars
            if "SUPABASE_URL" in os.environ:
                del os.environ["SUPABASE_URL"]
            if "SUPABASE_KEY" in os.environ:
                del os.environ["SUPABASE_KEY"]
            
            result = authenticate_user("user@company.com", "password")
            assert result is None
        finally:
            # Restore env vars
            if original_url:
                os.environ["SUPABASE_URL"] = original_url
            if original_key:
                os.environ["SUPABASE_KEY"] = original_key


class TestVerifyToken:
    """Tests for verify_token function"""
    
    @patch('auth.requests.get')
    @patch('auth.resolve_user_slot_context')
    def test_verify_token_success(self, mock_resolve, mock_get):
        """Test successful token verification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-id-123",
            "email": "user@company.com",
            "user_metadata": {
                "name": "Test User",
                "region": "R06 JABODEBEK",
                "role": "viewer"
            }
        }
        mock_get.return_value = mock_response
        
        mock_resolve.return_value = {
            "name": "Test User",
            "region": "R06 JABODEBEK",
            "role": "viewer"
        }
        
        result = verify_token("valid.token.here")
        
        assert result is not None
        assert result["email"] == "user@company.com"
        assert result["region"] == "R06 JABODEBEK"
    
    @patch('auth.requests.get')
    def test_verify_token_invalid(self, mock_get):
        """Test token verification with invalid token"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid.token")
        
        assert exc_info.value.status_code == 401
    
    @patch('auth.requests.get')
    def test_verify_token_missing_user_id(self, mock_get):
        """Test token verification with malformed response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "user@company.com"
            # Missing 'id' field
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token("token.without.id")
        
        assert exc_info.value.status_code == 401


class TestGetUserRegion:
    """Tests for get_user_region dependency"""
    
    @patch('auth.verify_token')
    def test_get_user_region_success(self, mock_verify):
        """Test getting user region from token"""
        mock_verify.return_value = {
            "email": "user@company.com",
            "region": "R06 JABODEBEK"
        }
        
        from fastapi import Header
        result = get_user_region("Bearer test.token")
        
        assert result == "R06 JABODEBEK"
    
    @patch('auth.verify_token')
    def test_get_user_region_admin(self, mock_verify):
        """Test admin user with ALL region"""
        mock_verify.return_value = {
            "email": "admin@company.com",
            "region": "ALL"
        }
        
        result = get_user_region("Bearer admin.token")
        
        assert result == "ALL"
    
    @patch('auth.verify_token')
    def test_get_user_region_no_region(self, mock_verify):
        """Test user without region defaults to ALL"""
        mock_verify.return_value = {
            "email": "user@company.com"
            # No region field
        }
        
        result = get_user_region("Bearer token")
        
        assert result == "ALL"
    
    def test_get_user_region_missing_header(self):
        """Test missing authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            get_user_region(None)
        
        assert exc_info.value.status_code == 401
    
    def test_get_user_region_invalid_scheme(self):
        """Test invalid authorization scheme"""
        with pytest.raises(HTTPException) as exc_info:
            get_user_region("InvalidScheme token")
        
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Tests for get_current_user dependency"""
    
    @patch('auth.verify_token')
    def test_get_current_user_success(self, mock_verify):
        """Test getting current user from token"""
        mock_user = {
            "email": "user@company.com",
            "name": "Test User",
            "region": "R06 JABODEBEK",
            "role": "viewer"
        }
        mock_verify.return_value = mock_user
        
        result = get_current_user("Bearer test.token")
        
        assert result == mock_user
        mock_verify.assert_called_once_with("test.token")
    
    def test_get_current_user_missing_header(self):
        """Test missing authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None)
        
        assert exc_info.value.status_code == 401


class TestResolveUserSlotContext:
    """Tests for resolve_user_slot_context function"""
    
    @patch('auth.supabase_request')
    @patch('auth.get_bigquery_service')
    def test_resolve_user_slot_context_success(self, mock_bq, mock_supabase):
        """Test successful slot context resolution"""
        # Mock employee lookup
        mock_supabase.side_effect = [
            {"data": [{"nik": "NIK001", "full_name": "Test User"}]},  # Employee
            {"data": [{"slot_code": "SL-001"}]},  # Assignment
            {"data": [{
                "slot_code": "SL-001",
                "role": "viewer",
                "scope": "REGION",
                "scope_id": "R06 JABODEBEK"
            }]},  # Slot
            {"data": [{"name": "JABODEBEK", "grbm_code": "GRBM01"}]}  # Region
        ]
        
        # Mock BigQuery
        mock_bq_service = Mock()
        mock_bq_service.project_id = "test-project"
        mock_bq_service.dataset = "test-dataset"
        mock_bq_service.client.query.return_value.to_dataframe.return_value = Mock()
        mock_bq_service.client.query.return_value.to_dataframe.return_value.empty = True
        mock_bq.return_value = mock_bq_service
        
        result = resolve_user_slot_context("user@company.com")
        
        assert result is not None
        assert result.get("name") == "Test User"
        assert result.get("nik") == "NIK001"
        assert result.get("slot_code") == "SL-001"
    
    @patch('auth.supabase_request')
    def test_resolve_user_slot_context_no_employee(self, mock_supabase):
        """Test when employee not found"""
        mock_supabase.return_value = {"data": []}
        
        result = resolve_user_slot_context("notfound@company.com")
        
        assert result == {}
    
    @patch('auth.supabase_request')
    def test_resolve_user_slot_context_no_assignment(self, mock_supabase):
        """Test when employee has no active assignment"""
        mock_supabase.side_effect = [
            {"data": [{"nik": "NIK001", "full_name": "Test User"}]},  # Employee
            {"data": []}  # No assignment
        ]
        
        result = resolve_user_slot_context("user@company.com")
        
        assert result.get("name") == "Test User"
        assert result.get("nik") == "NIK001"
        assert "slot_code" not in result
