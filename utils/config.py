from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./biointel.db",
        env="DATABASE_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Free AI Configuration
    USE_FREE_AI: bool = Field(default=True, env="USE_FREE_AI")
    HUGGINGFACE_CACHE_DIR: str = Field(default="/tmp/huggingface", env="HUGGINGFACE_CACHE_DIR")
    TORCH_CACHE_DIR: str = Field(default="/tmp/torch", env="TORCH_CACHE_DIR")
    
    # Free Bioinformatics APIs
    PUBMED_BASE_URL: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils", env="PUBMED_BASE_URL")
    UNIPROT_BASE_URL: str = Field(default="https://rest.uniprot.org", env="UNIPROT_BASE_URL")
    ENSEMBL_BASE_URL: str = Field(default="https://rest.ensembl.org", env="ENSEMBL_BASE_URL")
    STRING_BASE_URL: str = Field(default="https://string-db.org/api", env="STRING_BASE_URL")
    KEGG_BASE_URL: str = Field(default="https://rest.kegg.jp", env="KEGG_BASE_URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: list = Field(
        default=["csv", "xlsx", "xls", "pdf", "txt"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Reports
    REPORTS_DIR: str = Field(default="/tmp/biointel_reports", env="REPORTS_DIR")
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # CORS
    CORS_ORIGINS: list = Field(
        default=["http://localhost:3000", "https://biointel.ai"],
        env="CORS_ORIGINS"
    )
    
    # Data Processing
    MAX_GENES: int = Field(default=50000, env="MAX_GENES")
    MAX_SAMPLES: int = Field(default=10000, env="MAX_SAMPLES")
    MAX_GENES_PER_ANALYSIS: int = Field(default=1000, env="MAX_GENES_PER_ANALYSIS")
    
    # Literature Processing
    MAX_PAPER_LENGTH: int = Field(default=100000, env="MAX_PAPER_LENGTH")  # characters
    
    # Workflow Processing
    DEFAULT_ANALYSIS_TIMEOUT: int = Field(default=3600, env="DEFAULT_ANALYSIS_TIMEOUT")  # seconds
    MAX_CONCURRENT_ANALYSES: int = Field(default=10, env="MAX_CONCURRENT_ANALYSES")
    ENABLE_BACKGROUND_PROCESSING: bool = Field(default=True, env="ENABLE_BACKGROUND_PROCESSING")
    
    # Enterprise Features
    ENABLE_TEAMS: bool = Field(default=True, env="ENABLE_TEAMS")
    ENABLE_API_KEYS: bool = Field(default=True, env="ENABLE_API_KEYS")
    MAX_TEAM_MEMBERS: int = Field(default=100, env="MAX_TEAM_MEMBERS")
    MAX_WORKSPACES_PER_TEAM: int = Field(default=20, env="MAX_WORKSPACES_PER_TEAM")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Cache
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS: dict = Field(default={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    })
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    # Background Tasks
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Data Retention
    DATA_RETENTION_DAYS: int = Field(default=90, env="DATA_RETENTION_DAYS")
    
    # API Versioning
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")
    
    # Feature Flags
    ENABLE_ANALYTICS: bool = Field(default=True, env="ENABLE_ANALYTICS")
    ENABLE_CACHING: bool = Field(default=True, env="ENABLE_CACHING")
    ENABLE_RATE_LIMITING: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
class TestSettings(Settings):
    """Test environment settings"""
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    
def get_settings_by_env(env: str = None) -> Settings:
    """Get settings based on environment"""
    env = env or os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestSettings()
    else:
        return DevelopmentSettings()