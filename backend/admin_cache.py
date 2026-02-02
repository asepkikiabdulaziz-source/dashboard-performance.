"""
Admin endpoints for cache management
Allows administrators to monitor and manage cache
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from auth import get_current_user
from rbac import require_permission
from user_context_cache import get_cache_stats, clear_all_cache, invalidate_user_context
from zone_resolution_service import get_zone_cache_stats
from logger import get_logger

logger = get_logger("admin_cache")

router = APIRouter(prefix="/api/admin/cache", tags=["admin-cache"])


@router.get("/stats")
async def get_cache_stats_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(require_permission('admin.cache.view'))
):
    """
    Get cache statistics for monitoring
    """
    try:
        user_cache_stats = get_cache_stats()
        zone_cache_stats = get_zone_cache_stats()
        
        # Get leaderboard cache stats if available
        leaderboard_cache_stats = {}
        try:
            from main import cache_manager
            if cache_manager:
                leaderboard_cache_stats = cache_manager.get_cache_info()
        except:
            pass
        
        return {
            "user_context_cache": user_cache_stats,
            "zone_cache": zone_cache_stats,
            "leaderboard_cache": leaderboard_cache_stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_cache_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(require_permission('admin.cache.manage'))
):
    """
    Clear all caches (use with caution)
    """
    try:
        clear_all_cache()
        logger.warning(f"Cache cleared by admin: {current_user.get('email')}")
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate/{email}")
async def invalidate_user_cache(
    email: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(require_permission('admin.cache.manage'))
):
    """
    Invalidate cache for a specific user (e.g., after assignment change)
    """
    try:
        invalidate_user_context(email)
        logger.info(f"Cache invalidated for {email} by admin: {current_user.get('email')}")
        return {"message": f"Cache invalidated for {email}"}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
