"""
Configuration Management
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = True
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://192.168.1.81:11434"
    OLLAMA_MODEL: str = "sqlcoder:latest"
    OLLAMA_TIMEOUT: int = 300
    
    # Database - PostgreSQL (Production) or SQLite (Development)
    DATABASE_TYPE: str = "postgresql"  # postgresql or sqlite
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = "192.168.1.81"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_sql_optimizer_observability"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin123"
    
    # SQLite Configuration (Fallback for development)
    SQLITE_PATH: str = "./app/db/observability.db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL based on DATABASE_TYPE"""
        if self.DATABASE_TYPE == "postgresql":
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            return f"sqlite:///{self.SQLITE_PATH}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ENCRYPTION_KEY: str = "your-encryption-key-change-this-in-production"
    
    # Monitoring
    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL_MINUTES: int = 60
    MAX_QUERIES_PER_POLL: int = 100
    
    # Safety
    ENABLE_DDL_EXECUTION: bool = False
    BUSINESS_HOURS_ONLY: bool = False
    MAX_DDL_EXECUTION_TIME_SECONDS: int = 300
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
