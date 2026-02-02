"""
Security Middleware
Adds security headers and rate limiting
"""
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import time
from collections import defaultdict
from datetime import datetime, timedelta
from config import Config
from logger import get_logger

logger = get_logger("security_middleware")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server header (hide server info)
        if "server" in response.headers:
            del response.headers["server"]
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.requests: dict = defaultdict(list)
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leak"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = current_time - 3600  # Keep last hour
            for key in list(self.requests.keys()):
                self.requests[key] = [
                    req_time for req_time in self.requests[key]
                    if req_time > cutoff_time
                ]
                if not self.requests[key]:
                    del self.requests[key]
            self.last_cleanup = current_time
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from token if available
        # Otherwise use IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return ip
    
    def _check_rate_limit(self, client_id: str):
        """Check if client has exceeded rate limit"""
        if not Config.RATE_LIMIT_ENABLED:
            return True, None
        
        current_time = time.time()
        
        # Clean up old entries periodically
        self._cleanup_old_entries()
        
        # Get request times for this client
        request_times = self.requests[client_id]
        
        # Remove requests older than 1 hour
        one_hour_ago = current_time - 3600
        request_times[:] = [t for t in request_times if t > one_hour_ago]
        
        # Check per-minute limit
        one_minute_ago = current_time - 60
        recent_requests = [t for t in request_times if t > one_minute_ago]
        if len(recent_requests) >= Config.RATE_LIMIT_PER_MINUTE:
            return False, f"Rate limit exceeded: {Config.RATE_LIMIT_PER_MINUTE} requests per minute"
        
        # Check per-hour limit
        if len(request_times) >= Config.RATE_LIMIT_PER_HOUR:
            return False, f"Rate limit exceeded: {Config.RATE_LIMIT_PER_HOUR} requests per hour"
        
        # Add current request
        request_times.append(current_time)
        
        return True, None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        allowed, error_msg = self._check_rate_limit(client_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id}: {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": error_msg,
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        request_times = self.requests[client_id]
        one_minute_ago = time.time() - 60
        recent_count = len([t for t in request_times if t > one_minute_ago])
        
        response.headers["X-RateLimit-Limit"] = str(Config.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, Config.RATE_LIMIT_PER_MINUTE - recent_count))
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling and logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "client": request.client.host if request.client else "unknown"
                }
            )
            
            # Return generic error in production, detailed in development
            if Config.IS_PRODUCTION:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal server error"}
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Internal server error",
                        "error": str(e),
                        "type": type(e).__name__
                    }
                )
