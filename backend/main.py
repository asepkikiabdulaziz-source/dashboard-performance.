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

# FORCE LOAD ENV
load_dotenv()

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

app = FastAPI(title="Professional Dashboard", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Static File Serving (Production) ============
# Serve frontend dist folder if it exists (for Docker/Production)
frontend_path = os.path.join(os.getcwd(), "dist")
if not os.path.exists(frontend_path):
    # Try alternate location
    frontend_path = os.path.join(os.getcwd(), "frontend", "dist")

if os.path.exists(frontend_path) and os.path.isdir(frontend_path):
    print(f"📦 Production mode: Serving static files from {frontend_path}")
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Exclude API calls from being caught by the wildcard
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
            
        file_path = os.path.join(frontend_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    print("🚀 Development mode: Static file serving disabled (use Vite dev server)")

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
# Global cache instance (initialized on startup)
cache_manager: Optional[LeaderboardCache] = None

# Initialize data generator and BigQuery service
data_generator = None
bigquery_service = None

try:
    print("🔄 Initializing Mock Data Generator...")
    data_generator = get_data_generator()
    print("✅ Mock Data Generator initialized")
except Exception as e:
    print(f"⚠️ Failed to initialize Mock Data Generator: {e}")
    with open("startup_error.log", "w") as f:
        f.write(f"MockData Init Result: {str(e)}")

try:
    print("🔄 Initializing BigQuery Service...")
    bigquery_service = get_bigquery_service()
    print("✅ BigQuery Service initialized")
except Exception as e:
    print(f"⚠️ Failed to initialize BigQuery Service: {e}")

# Include admin routes
app.include_router(admin_router)
app.include_router(admin_employees_router)
app.include_router(admin_master_router)
app.include_router(admin_slots_router)

# Startup event to initialize cache
@app.on_event("startup")
async def startup_event():
    """Initialize cache on startup"""
    global cache_manager
    print("🚀 Initializing smart cache system...")
    try:
        cache_manager = LeaderboardCache(bigquery_service)
        print("✅ Cache initialized (background loading started)")
    except Exception as e:
        print(f"❌ Failed to initialize cache: {e}")

# Pydantic models



@app.get("/api/auth/me", response_model=UserInfo)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
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

@app.get("/api/dashboard/sales")
async def get_sales_data(user_region: str = Depends(get_user_region)):
    """
    Get sales data filtered by user's region
    Row-Level Security applied automatically
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


@app.get("/api/dashboard/kpis")
async def get_kpis(user_region: str = Depends(get_user_region)):
    """Get KPIs filtered by user's region"""
    return data_generator.get_kpis(user_region)


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

@app.get("/api/leaderboard")
async def get_leaderboard(
    limit: Optional[int] = None,
    division: Optional[str] = None,
    region: Optional[str] = None,  # Query param for admin to override region
    user_region: str = Depends(get_user_region)
):
    """
    Get salesman leaderboard with RLS (cached)
    
    Query params:
    - limit: Maximum number of results (optional)
    - division: Filter by division (optional)
    - region: Override region (admin only, optional)
    """
    try:
        # RLS SECURITY CHECK:
        # Only ADMIN (user_region="ALL") can override the region via query param.
        # Regular users are strictly locked to their token's region.
        target_region = user_region
        if user_region == "ALL" and region:
            target_region = region
            
        print(f"🔒 RLS ENFORCED: User={user_region} | Requested={region} | Final Access={target_region}")
        
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
    """Get top performing salesman with RLS"""
    try:
        return bigquery_service.get_top_performers(user_region, limit)
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
    """Get KPIs from BigQuery (real data)"""
    try:
        return bigquery_service.get_kpis(user_region)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching KPIs: {str(e)}"
        )


@app.get("/api/dashboard/sales-trend-bigquery")
async def get_sales_trend_bigquery(user_region: str = Depends(get_user_region)):
    """Get sales trend from BigQuery (P1-P4)"""
    try:
        df = bigquery_service.get_sales_trend(user_region)
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sales trend: {str(e)}"
        )


@app.get("/api/dashboard/region-comparison-bigquery")
async def get_region_comparison_bigquery(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get region comparison from BigQuery
    Only available for admin users
    """
    if current_user["region"] != "ALL":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can access region comparison"
        )
    
    try:
        df = bigquery_service.get_region_comparison()
        return df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching region comparison: {str(e)}"
        )




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
             
        data = bigquery_service.get_competition_ranks(
            level=level, 
            competition_id=competition_id, 
            region=target_region,
            role=current_user.get('role', 'viewer'),
            user_nik=current_user.get('nik'),
            scope=current_user.get('scope'),
            scope_id=current_user.get('scope_id'),
            zona_rbm=current_user.get('zona_rbm'),
            zona_bm=current_user.get('zona_bm')
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

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "message": "Dashboard Performance API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "auth": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/api/debug/assignments")
async def debug_check_assignments():
    try:
        from supabase_client import get_supabase_client
        sb = get_supabase_client()
        res = sb.schema('hr').table('assignments').select("*").limit(1).execute()
        return {"status": "found", "columns": list(res.data[0].keys()) if res.data else "empty_table"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
