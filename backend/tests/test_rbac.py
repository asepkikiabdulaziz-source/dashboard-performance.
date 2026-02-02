"""
Tests for RBAC module (rbac.py)
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from rbac import get_role_permissions, require_permission, ROLE_PERMISSIONS_CACHE


class TestGetRolePermissions:
    """Tests for get_role_permissions function"""
    
    def test_get_role_permissions_cache_hit(self):
        """Test that cached permissions are returned"""
        # Clear cache first
        ROLE_PERMISSIONS_CACHE.clear()
        
        # Set cache
        ROLE_PERMISSIONS_CACHE["viewer"] = ["dashboard.view", "leaderboard.view"]
        
        result = get_role_permissions("viewer")
        
        assert result == ["dashboard.view", "leaderboard.view"]
    
    @patch('rbac.supabase_request')
    def test_get_role_permissions_cache_miss(self, mock_supabase):
        """Test fetching permissions from database when not cached"""
        ROLE_PERMISSIONS_CACHE.clear()
        
        mock_supabase.return_value = {
            "data": [
                {"permission_code": "dashboard.view"},
                {"permission_code": "leaderboard.view"}
            ]
        }
        
        result = get_role_permissions("viewer")
        
        assert result == ["dashboard.view", "leaderboard.view"]
        assert "viewer" in ROLE_PERMISSIONS_CACHE
        mock_supabase.assert_called_once()
    
    @patch('rbac.supabase_request')
    def test_get_role_permissions_empty_result(self, mock_supabase):
        """Test when role has no permissions"""
        ROLE_PERMISSIONS_CACHE.clear()
        
        mock_supabase.return_value = {"data": []}
        
        result = get_role_permissions("empty_role")
        
        assert result == []
    
    @patch('rbac.supabase_request')
    def test_get_role_permissions_error_handling(self, mock_supabase):
        """Test error handling when database call fails"""
        ROLE_PERMISSIONS_CACHE.clear()
        
        mock_supabase.side_effect = Exception("Database error")
        
        result = get_role_permissions("error_role")
        
        assert result == []


class TestRequirePermission:
    """Tests for require_permission decorator"""
    
    @patch('rbac.get_current_user')
    @patch('rbac.get_role_permissions')
    def test_require_permission_success(self, mock_get_perms, mock_get_user):
        """Test successful permission check"""
        mock_get_user.return_value = {
            "email": "user@company.com",
            "role": "viewer"
        }
        mock_get_perms.return_value = ["dashboard.view", "leaderboard.view"]
        
        checker = require_permission("dashboard.view")
        result = checker()
        
        assert result is True
        mock_get_perms.assert_called_once_with("viewer")
    
    @patch('rbac.get_current_user')
    def test_require_permission_super_admin_bypass(self, mock_get_user):
        """Test that super_admin bypasses permission check"""
        mock_get_user.return_value = {
            "email": "admin@company.com",
            "role": "super_admin"
        }
        
        checker = require_permission("any.permission")
        result = checker()
        
        assert result is True
    
    @patch('rbac.get_current_user')
    def test_require_permission_no_role(self, mock_get_user):
        """Test when user has no role"""
        mock_get_user.return_value = {
            "email": "user@company.com"
            # No role field
        }
        
        checker = require_permission("dashboard.view")
        
        with pytest.raises(HTTPException) as exc_info:
            checker()
        
        assert exc_info.value.status_code == 403
        assert "no role" in exc_info.value.detail.lower()
    
    @patch('rbac.get_current_user')
    @patch('rbac.get_role_permissions')
    def test_require_permission_denied(self, mock_get_perms, mock_get_user):
        """Test when user lacks required permission"""
        mock_get_user.return_value = {
            "email": "user@company.com",
            "role": "viewer"
        }
        mock_get_perms.return_value = ["dashboard.view"]  # Missing "admin.manage"
        
        checker = require_permission("admin.manage")
        
        with pytest.raises(HTTPException) as exc_info:
            checker()
        
        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.detail
    
    @patch('rbac.get_current_user')
    def test_require_permission_super_admin_case_insensitive(self, mock_get_user):
        """Test that SUPER_ADMIN (uppercase) also bypasses"""
        mock_get_user.return_value = {
            "email": "admin@company.com",
            "role": "SUPER_ADMIN"
        }
        
        checker = require_permission("any.permission")
        result = checker()
        
        assert result is True
