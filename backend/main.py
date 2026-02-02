"""
FastAPI backend for Professional Dashboard
Provides RESTful API with Row-Level Security
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import timedelta
from dotenv import load_dotenv
import os
import logging

# FORCE LOAD ENV
load_dotenv()

# Load configuration
from config import Config

# Setup logging
from logger import get_logger
logger = get_logger("main")

from auth import (
    authenticate_user,
    get_user_region,
    get_current_user
)
from rbac import get_role_permissions
from mock_data import get_data_generator
from bigquery_service import get_bigquery_service
from cache_manager import LeaderboardCache
from admin_routes import router as admin_router
from admin_employees import router as admin_employees_router
from admin_master import router as admin_master_router
from admin_slots import router as admin_slots_router
from admin_cache import router as admin_cache_router

app = FastAPI(
    title=Config.API_TITLE,
    description="""
    Professional analytics dashboard API with Row-Level Security (RLS) and Role-Based Access Control (RBAC).
    
    ## Features
    
    - **Authentication**: JWT-based authentication with Supabase
    - **Row-Level Security**: Automatic data filtering by user region
    - **RBAC**: Fine-grained permission-based access control
    - **BigQuery Integration**: Real-time data from Google BigQuery
    - **Caching**: High-performance in-memory caching for fast responses
    
    ## Authentication
    
    All endpoints (except `/api/auth/login`) require a Bearer token in the Authorization header.
    
    ```
    Authorization: Bearer <your_jwt_token>
    ```
    
    ## Row-Level Security
    
    Users automatically see only data for their assigned region. Admin users (region="ALL") can access all regions.
    
    ## API Documentation
    
    - **Swagger UI**: Available at `/docs` (interactive API explorer)
    - **ReDoc**: Available at `/redoc` (alternative documentation)
    - **OpenAPI Schema**: Available at `/openapi.json`
    """,
    version=Config.API_VERSION,
    docs_url=Config.API_DOCS_URL,
    redoc_url=Config.API_REDOC_URL,
    openapi_url="/openapi.json" if not Config.IS_PRODUCTION else None,
    contact={
        "name": "Dashboard Performance API",
    },
    license_info={
        "name": "MIT",
    },
)

# Security Middleware (add first, so it processes responses last)
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware
)

if Config.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# CORS Middleware - Use configuration from Config
cors_config = Config.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)


# ============ Application Configuration ============

# ... (skip cache init) ...

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserInfo(BaseModel):
    email: str
    region: str
    role: str
    name: str
    permissions: List[str] = []


# ... (skip init) ...


# ============ Authentication Endpoints ============

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT token
    """
    user = authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Inject permissions
    role = user.get('role', 'viewer')
    perms = get_role_permissions(role)
    user['permissions'] = perms
    
    return {
        "access_token": user["access_token"],
        "token_type": "bearer",
        "user": user
    }
# Initialize data generator and BigQuery service
data_generator = None
bigquery_service = None
cache_manager = None  # Global cache manager

try:
    logger.info("🔄 Initializing Mock Data Generator...")
    data_generator = get_data_generator()
    logger.info("✅ Mock Data Generator initialized")
except Exception as e:
    logger.error(f"⚠️ Failed to initialize Mock Data Generator: {e}", exc_info=True)

try:
    logger.info("🔄 Initializing BigQuery Service...")
    bigquery_service = get_bigquery_service()
    logger.info("✅ BigQuery Service initialized")
except Exception as e:
    logger.error(f"⚠️ Failed to initialize BigQuery Service: {e}", exc_info=True)

# Include admin routes
app.include_router(admin_router)
app.include_router(admin_employees_router)
app.include_router(admin_master_router)
app.include_router(admin_slots_router)
app.include_router(admin_cache_router)

# Startup event to initialize cache
@app.on_event("startup")
async def startup_event():
    """Initialize cache and services on startup"""
    global cache_manager
    
    # Initialize user context cache (with optional Redis)
    try:
        from user_context_cache import init_redis
        redis_url = os.getenv("REDIS_URL")  # e.g., "redis://localhost:6379"
        init_redis(redis_url)
    except Exception as e:
        logger.warning(f"Redis initialization skipped: {e}")
    
    # Initialize leaderboard cache
    logger.info("🚀 Initializing smart cache system...")
    try:
        cache_manager = LeaderboardCache(bigquery_service)
        logger.info("✅ Cache initialized (background loading started)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}", exc_info=True)
    
    # Pre-load zone mappings for common regions (background)
    try:
        from zone_resolution_service import preload_zones_for_regions
        # Get list of regions from cache or BigQuery
        if cache_manager:
            regions = cache_manager.get_regions()
            if regions:
                # Pre-load zones in background (non-blocking)
                import threading
                thread = threading.Thread(target=lambda: preload_zones_for_regions(regions[:10]))  # Top 10 regions
                thread.daemon = True
                thread.start()
                logger.info(f"✅ Zone pre-loading started for {min(10, len(regions))} regions")
    except Exception as e:
        logger.warning(f"Zone pre-loading skipped: {e}")

# Pydantic models



@app.get("/api/auth/me", response_model=UserInfo, tags=["Authentication"])
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns the user's profile including:
    - Email and name
    - Assigned region
    - Role and permissions
    - Scope information (for competition access)
    
    **Authentication Required:** Yes (Bearer token)
    """
    return current_user


@app.get("/api/auth/demo-users")
async def get_demo_users():
    """Get list of demo users for testing (remove in production)"""
    return [
        {
            "email": email,
            "password": user["password"],
            "region": user["region"],
            "role": user["role"],
            "name": user["name"]
        }
        for email, user in DEMO_USERS.items()
    ]


# ============ Dashboard Data Endpoints (with RLS) ============

@app.get("/api/dashboard/sales", tags=["Dashboard"])
async def get_sales_data(user_region: str = Depends(get_user_region)):
    """
    Get sales data filtered by user's region.
    
    **Row-Level Security:** Automatically filters data based on user's assigned region.
    Admin users (region="ALL") see all regions.
    
    **Returns:** List of sales records with:
    - Date/week information
    - Revenue amounts
    - Region-specific data
    
    **Authentication Required:** Yes
    """
    df = data_generator.get_sales_data(user_region)
    return df.to_dict(orient='records')


@app.get("/api/dashboard/targets")
async def get_target_data(user_region: str = Depends(get_user_region)):
    """Get target vs actual data with RLS"""
    try:
        if data_generator is None:
            raise Exception("Data Generator is not initialized")
        df = data_generator.get_target_data(user_region)
        return df.to_dict(orient='records')
    except Exception as e:
        with open("runtime_error.log", "a") as f:
            f.write(f"Target Data Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/forecast")
async def get_forecast_data(user_region: str = Depends(get_user_region)):
    """Get forecast data with RLS"""
    df = data_generator.get_forecast_data(user_region)
    return df.to_dict(orient='records')


@app.get("/api/dashboard/kpis", tags=["Dashboard"])
async def get_kpis(user_region: str = Depends(get_user_region)):
    """
    Get Key Performance Indicators (KPIs) for the user's region.
    
    **Returns:**
    - `total_revenue`: Total revenue for the period
    - `total_target`: Target revenue
    - `achievement_rate`: Percentage of target achieved
    - `growth_rate`: Growth percentage compared to previous period
    - `next_month_forecast`: Forecasted revenue for next month
    - `total_salesman`: Number of salesmen in region
    - `avg_customer_base`: Average customer base
    - `avg_roa`: Average Return on Assets
    
    **Performance:** Data is served from high-speed in-memory cache.
    
    **Authentication Required:** Yes
    """
    return cache_manager.get_kpis_cached(user_region)


@app.get("/api/dashboard/top-products")
async def get_top_products(
    limit: int = 5,
    user_region: str = Depends(get_user_region)
):
    """Get top products with RLS"""
    return data_generator.get_top_products(user_region, limit)


@app.get("/api/dashboard/region-comparison")
async def get_region_comparison(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get region comparison data
    Only available for admin users
    """
    if current_user["region"] != "ALL":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access region comparison"
        )
    
    return data_generator.get_region_comparison()


# ============ BigQuery Leaderboard Endpoints (NEW) ============

@app.get("/api/leaderboard", tags=["Leaderboard"])
async def get_leaderboard(
    limit: Optional[int] = None,
    division: Optional[str] = None,
    region: Optional[str] = None,  # Query param for admin to override region
    user_region: str = Depends(get_user_region)
):
    """
    Get salesman leaderboard with ranking and performance metrics.
    
    **Query Parameters:**
    - `limit` (optional): Maximum number of results to return
    - `division` (optional): Filter by division code
    - `region` (optional): Override region filter (admin only)
    
    **Row-Level Security:**
    - Regular users: Automatically filtered to their assigned region
    - Admin users: Can override region via `region` query parameter
    
    **Returns:** List of salesman records with:
    - Ranking position
    - Salesman name and NIK
    - Performance metrics (revenue, targets, achievement)
    - Region and division information
    
    **Performance:** Data is served from high-speed in-memory cache.
    
    **Authentication Required:** Yes
    """
    try:
        # RLS SECURITY CHECK:
        # Only ADMIN (user_region="ALL") can override the region via query param.
        # Regular users are strictly locked to their token's region.
        target_region = user_region
        if user_region == "ALL" and region:
            target_region = region
            
        logger.debug(f"🔒 RLS ENFORCED: User={user_region} | Requested={region} | Final Access={target_region}")
        
        # Get from cache (auto-checks cutoff_date)
        data = cache_manager.get_leaderboard(
            region=target_region,
            division=division,
            limit=limit
        )
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching leaderboard: {str(e)}"
        )

@app.get("/api/leaderboard/top-summary")
async def get_top_summary(
    user_region: str = Depends(get_user_region)
):
    """
    Get summary of Top 1 Salesman per Region (for Modal View).
    """
    return cache_manager.get_top_performers_summary(target_region=user_region)


@app.get("/api/leaderboard/top-performers")
async def get_top_performers_api(
    limit: int = 10,
    user_region: str = Depends(get_user_region)
):
    """Get top performing salesman with RLS (from high-speed cache)"""
    try:
        return cache_manager.get_top_performers_cached(user_region, limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching top performers: {str(e)}"
        )


@app.get("/api/leaderboard/divisions")
async def get_divisions_api(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get available divisions in user's region (from cache)"""
    try:
        divisions = cache_manager.get_divisions(current_user["region"])
        return {"divisions": divisions}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching divisions: {str(e)}"
        )


@app.get("/api/leaderboard/cutoff-date")
async def get_cutoff_date_api():
    """Get latest cut-off date"""
    try:
        cutoff_date = bigquery_service.get_cutoff_date()
        return {"cutoff_date": cutoff_date}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cutoff date: {str(e)}"
        )


@app.get("/api/leaderboard/regions")
async def get_regions_api(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get list of available regions (from cache)
    Admin gets all regions, regional users get only their region
    """
    try:
        if current_user["region"] == "ALL":
            # Admin - return all unique regions from cache
            regions_list = cache_manager.get_regions()
            
            # Format as expected by frontend
            regions = [
                {
                    "code": r,
                    "name": r,
                    "salesman_count": 0
                }
                for r in regions_list
            ]
            
            # PREPEND NATIONAL (ALL) option
            regions.insert(0, {
                "code": "ALL",
                "name": "NATIONAL (ALL)",
                "salesman_count": sum(r.get('salesman_count', 0) for r in regions)
            })
            
            return {"regions": regions}
        else:
            # Regional user: only their region
            return {
                "regions": [{
                    "code": current_user["region"],
                    "name": current_user["region"],
                    "salesman_count": 0  # Can be populated if needed
                }]
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching regions: {str(e)}"
        )


# ============ BigQuery KPIs (Using Real Data) ============

@app.get("/api/dashboard/kpis-bigquery")
async def get_kpis_bigquery(user_region: str = Depends(get_user_region)):
    """Get KPIs from BigQuery (redirected to high-speed cache)"""
    return cache_manager.get_kpis_cached(user_region)


@app.get("/api/dashboard/sales-trend-bigquery")
async def get_sales_trend_bigquery(user_region: str = Depends(get_user_region)):
    """Get sales trend from BigQuery (redirected to high-speed cache)"""
    return cache_manager.get_sales_trend_cached(user_region)


@app.get("/api/dashboard/region-comparison-bigquery")
async def get_region_comparison_bigquery(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get region comparison from BigQuery (redirected to high-speed cache)
    Only available for admin users
    """
    if current_user["region"] != "ALL":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access region comparison"
        )
    
    return cache_manager.get_region_comparison_cached()




@app.get("/api/competitions/list")
async def get_competitions_list(current_user: dict = Depends(get_current_user)):
    """Get list of available competitions"""
    from competition_config import COMPETITIONS
    return {"data": [
        {"id": k, "title": v["title"], "period": v.get("period", "")} 
        for k, v in COMPETITIONS.items()
    ]}


@app.get("/api/dashboard/competition/{competition_id}/{level}")
async def get_competition_ranks_v2(
    competition_id: str,
    level: str,
    region: Optional[str] = None,
    zona_bm: Optional[str] = None,
    zona_rbm: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get competition ranking for a specific competition
    """
    try:
        target_region = "ALL"
        if current_user.get("region") == "ALL":
             if region: target_region = region
        else:
             target_region = current_user.get("region", "ALL")
            # Fetch competition ranking data
        data = cache_manager.get_competition_ranks_cached(
            level=level, 
            competition_id=competition_id, 
            region=target_region,
            role=current_user.get('role', 'viewer'),
            user_nik=current_user.get('nik'),
            scope=current_user.get('scope'),
            scope_id=current_user.get('scope_id'),
            zona_rbm=zona_rbm or current_user.get('zona_rbm'),
            zona_bm=zona_bm or current_user.get('zona_bm')
        )
        
        # Fetch cutoff metadata
        metadata = bigquery_service.get_cutoff_metadata()
        
        return {
            "data": data,
            "metadata": metadata
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Backward compatibility
@app.get("/api/dashboard/competition/{level}")
async def get_competition_ranks_legacy(
    level: str,
    region: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Legacy endpoint wrapper for v2"""
    return await get_competition_ranks_v2("amo_jan_2026", level, region, current_user)

# ============ Health Check ============

@app.get("/health", tags=["System"], include_in_schema=True)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    **Returns:**
    - `status`: Overall system status
    - `cache`: Cache system information
    - `bq_auth`: BigQuery authentication status
    - `services`: Service operational status
    
    **Authentication Required:** No
    
    **Use Cases:**
    - Load balancer health checks
    - Monitoring system uptime
    - Debugging connection issues
    """
    return {
        "status": "healthy",
        "cache": cache_manager.get_cache_info() if cache_manager else "not_initialized",
        "bq_auth": {
            "method": "ADC" if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else "FILE",
            "file_exists": os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')) if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else False,
            "project_id": bigquery_service.project_id if bigquery_service else None
        },
        "services": {
            "api": "operational",
            "auth": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/api/debug/bq", include_in_schema=False)
async def debug_bigquery(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Diagnostic endpoint for BigQuery health (Super Admin only)
    Hidden from API documentation. Only available in development mode.
    """
    # Only allow in development mode
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    results = {
        "project_id": bigquery_service.project_id,
        "dataset": bigquery_service.dataset,
        "table": bigquery_service.table,
        "conn": "UNKNOWN",
        "error": None,
        "dataset_exists": False,
        "row_count": 0,
        "available_datasets": [],
        "auth_method": "ADC" if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else f"FILE: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}",
        "credentials_file_exists": os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')) if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') else False
    }
    
    try:
        datasets = list(bigquery_service.client.list_datasets())
        results["conn"] = "OK"
        results["available_datasets"] = [d.dataset_id for d in datasets]
        results["dataset_exists"] = bigquery_service.dataset in results["available_datasets"]
        
        if results["dataset_exists"]:
            query = f"SELECT COUNT(*) as total FROM {bigquery_service.full_table_id}"
            count_res = bigquery_service.client.query(query).to_dataframe()
            results["row_count"] = int(count_res.iloc[0]['total'])
    except Exception as e:
        results["conn"] = "FAILED"
        results["error"] = str(e)
        
    return results

@app.get("/api/debug/assignments", include_in_schema=False)
async def debug_check_assignments(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Debug endpoint for checking assignments (Super Admin only)
    Hidden from API documentation. Only available in development mode.
    """
    # Only allow in development mode
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        from supabase_client import get_supabase_client
        sb = get_supabase_client()
        res = sb.schema('hr').table('assignments').select("*").limit(1).execute()
        return {"status": "found", "data_sample": res.data[0] if res.data else "empty"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============ Static File Serving (Production) ============
# MUST BE AT THE END to avoid shadowing API routes
frontend_path = os.path.join(os.getcwd(), "dist")
if not os.path.exists(frontend_path):
    frontend_path = os.path.join(os.getcwd(), "frontend", "dist")

if os.path.exists(frontend_path) and os.path.isdir(frontend_path):
    logger.info(f"📦 Production mode: Serving static files from {frontend_path}")
    # Mount assets folder
    if os.path.exists(os.path.join(frontend_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # If it reaches here, it didn't match any API route above
        # If it's an /api/ call, it's definitely a 404
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
            
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Fallback to index.html for SPA routing
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    logger.info("🚀 Development mode: Static file serving disabled")
