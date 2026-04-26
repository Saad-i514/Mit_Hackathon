"""
Configuration module for AI Scientist Platform
Loads and validates environment variables
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Supabase Configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_db_password: str = ""
    
    # External APIs
    serper_api_key: str = ""
    semantic_scholar_api_key: str = ""
    protocols_io_token: str = ""
    
    # LangSmith Configuration
    langchain_tracing_v2: str = "false"
    langchain_api_key: str = ""
    langchain_project: str = "ai-scientist-platform"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    
    # Application Configuration
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app_env.lower() == "development"


# Global settings instance
settings = Settings()
