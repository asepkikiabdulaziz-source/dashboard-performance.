"""
Production Configuration Management
Handles environment-specific settings and validation
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
from logger import get_logger

logger = get_logger("config")

# Load environment variables
load_dotenv()

class Config:
    """Application configuration with environment-based defaults"""
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    IS_PRODUCTION = ENVIRONMENT.lower() == "production"
    IS_DEVELOPMENT = not IS_PRODUCTION
    
    # API Configuration
    API_TITLE = os.getenv("API_TITLE", "Dashboard Performance API")
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    API_DOCS_URL = "/docs" if not IS_PRODUCTION else None  # Disable docs in production
    API_REDOC_URL = "/redoc" if not IS_PRODUCTION else None
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = []
    if os.getenv("ALLOWED_ORIGINS"):
        ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS").split(",") if origin.strip()]
    else:
        # Default to localhost for development
        ALLOWED_ORIGINS = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else []
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # BigQuery
    BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
    BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")
    
    # Redis (Optional)
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO" if IS_PRODUCTION else "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    LOG_ERROR_FILE = os.getenv("LOG_ERROR_FILE", "logs/error.log")
    
    # Cache
    CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "15"))
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    @classmethod
    def validate(cls) -> List[str]:
        """Validate required configuration and return list of missing variables"""
        missing = []
        
        required_vars = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "SUPABASE_SERVICE_ROLE_KEY": cls.SUPABASE_SERVICE_ROLE_KEY,
            "BIGQUERY_PROJECT_ID": cls.BIGQUERY_PROJECT_ID,
            "BIGQUERY_DATASET": cls.BIGQUERY_DATASET,
        }
        
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing.append(var_name)
        
        if cls.IS_PRODUCTION:
            # Additional production requirements
            if not cls.ALLOWED_ORIGINS or cls.ALLOWED_ORIGINS == ["http://localhost:5173"]:
                missing.append("ALLOWED_ORIGINS (must be set for production)")
            
            if cls.SECRET_KEY == "change-me-in-production":
                missing.append("SECRET_KEY (must be changed for production)")
        
        return missing
    
    @classmethod
    def get_cors_config(cls) -> dict:
        """Get CORS configuration"""
        return {
            "allow_origins": cls.ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["*"],
        }
    
    @classmethod
    def log_config_summary(cls):
        """Log configuration summary (without sensitive data)"""
        logger.info("=" * 60)
        logger.info("Configuration Summary")
        logger.info("=" * 60)
        logger.info(f"Environment: {cls.ENVIRONMENT}")
        logger.info(f"Production Mode: {cls.IS_PRODUCTION}")
        logger.info(f"API Title: {cls.API_TITLE}")
        logger.info(f"API Version: {cls.API_VERSION}")
        logger.info(f"Docs Enabled: {cls.API_DOCS_URL is not None}")
        logger.info(f"CORS Origins: {len(cls.ALLOWED_ORIGINS)} configured")
        logger.info(f"Rate Limiting: {'Enabled' if cls.RATE_LIMIT_ENABLED else 'Disabled'}")
        logger.info(f"Cache Enabled: {cls.CACHE_ENABLED}")
        logger.info(f"Log Level: {cls.LOG_LEVEL}")
        logger.info("=" * 60)
        
        # Validate and warn
        missing = cls.validate()
        if missing:
            logger.warning(f"Missing required configuration: {', '.join(missing)}")
            if cls.IS_PRODUCTION:
                logger.error("Production deployment requires all configuration to be set!")
        else:
            logger.info("✅ All required configuration present")

# Initialize and validate on import
config = Config()
if config.IS_PRODUCTION:
    config.log_config_summary()
