"""
Deployment Configuration
Centralized configuration for deployment settings
All deployment-specific values should be set via environment variables
"""
import os
from typing import Optional
from logger import get_logger

logger = get_logger("deployment_config")


class DeploymentConfig:
    """Deployment-specific configuration"""
    
    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "asia-southeast2")
    GCP_SERVICE_NAME: str = os.getenv("GCP_SERVICE_NAME", "dashboard-performance")
    GCP_ARTIFACT_REPOSITORY: str = os.getenv("GCP_ARTIFACT_REPOSITORY", "dashboard-repo")
    
    # Cloud Run Configuration
    CLOUD_RUN_MEMORY: str = os.getenv("CLOUD_RUN_MEMORY", "1Gi")
    CLOUD_RUN_CPU: str = os.getenv("CLOUD_RUN_CPU", "1")
    CLOUD_RUN_MIN_INSTANCES: int = int(os.getenv("CLOUD_RUN_MIN_INSTANCES", "0"))
    CLOUD_RUN_MAX_INSTANCES: int = int(os.getenv("CLOUD_RUN_MAX_INSTANCES", "10"))
    CLOUD_RUN_TIMEOUT: int = int(os.getenv("CLOUD_RUN_TIMEOUT", "300"))
    CLOUD_RUN_PORT: int = int(os.getenv("CLOUD_RUN_PORT", "8080"))
    
    @classmethod
    def get_artifact_registry_path(cls, image_tag: str = "latest") -> str:
        """Get full Artifact Registry path for Docker image"""
        if not cls.GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID must be set")
        return f"{cls.GCP_REGION}-docker.pkg.dev/{cls.GCP_PROJECT_ID}/{cls.GCP_ARTIFACT_REPOSITORY}/{cls.GCP_SERVICE_NAME}:{image_tag}"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required deployment configuration"""
        missing = []
        
        # GCP_PROJECT_ID is required for deployment
        if not cls.GCP_PROJECT_ID:
            missing.append("GCP_PROJECT_ID")
        
        return missing
    
    @classmethod
    def log_config(cls):
        """Log deployment configuration (without sensitive data)"""
        logger.info("=" * 60)
        logger.info("Deployment Configuration")
        logger.info("=" * 60)
        logger.info(f"GCP Project ID: {cls.GCP_PROJECT_ID or 'NOT SET'}")
        logger.info(f"GCP Region: {cls.GCP_REGION}")
        logger.info(f"Service Name: {cls.GCP_SERVICE_NAME}")
        logger.info(f"Artifact Repository: {cls.GCP_ARTIFACT_REPOSITORY}")
        logger.info(f"Cloud Run Memory: {cls.CLOUD_RUN_MEMORY}")
        logger.info(f"Cloud Run CPU: {cls.CLOUD_RUN_CPU}")
        logger.info(f"Min Instances: {cls.CLOUD_RUN_MIN_INSTANCES}")
        logger.info(f"Max Instances: {cls.CLOUD_RUN_MAX_INSTANCES}")
        logger.info("=" * 60)


# Singleton instance
deployment_config = DeploymentConfig()
