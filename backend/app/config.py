# backend/app/config.py
"""
Application Configuration
=========================
This module handles all configuration settings for the Legal Assistant API.
We use pydantic-settings to load values from environment variables with 
sensible defaults for development.

Why use this approach?
- Security: Sensitive values (API keys, secrets) stay out of code
- Flexibility: Different settings for dev/staging/production
- Type safety: Pydantic validates and converts types automatically
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Each field can be overridden by setting an environment variable
    with the same name (case-insensitive).
    
    Example:
        Set DATABASE_URL in .env or environment to override the default.
    """
    
    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    APP_NAME: str = "AI Legal Assistant"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "An AI-powered legal assistant for Indian law"
    DEBUG: bool = True
    
    # API prefix for all routes
    API_V1_PREFIX: str = "/api/v1"
    
    # ============================================
    # SERVER SETTINGS
    # ============================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS: Origins allowed to call our API
    # In production, this should be your frontend domain only
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # ============================================
    # DATABASE SETTINGS
    # ============================================
    # Using SQLite for development (easy, no setup required)
    # Format: sqlite+aiosqlite:///./path/to/db.sqlite
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/legal_assistant.db"
    
    # For PostgreSQL in production, you would use:
    # DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/dbname"
    
    # ============================================
    # AUTHENTICATION SETTINGS
    # ============================================
    # Secret key for JWT signing - CHANGE THIS IN PRODUCTION!
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    
    # JWT Algorithm
    ALGORITHM: str = "HS256"
    
    # Token expiration time in minutes (24 hours = 1440 minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # ============================================
    # FILE UPLOAD SETTINGS
    # ============================================
    # Maximum file size in bytes (10 MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    
    # Upload directory paths
    UPLOAD_DIR: str = "./data/uploads"
    GENERATED_DIR: str = "./data/generated"
    KNOWLEDGE_BASE_DIR: str = "./data/knowledge_base"
    
    # ============================================
    # AI/LLM SETTINGS (will configure later)
    # ============================================
    # OpenAI API Key (optional - for production)
    OPENAI_API_KEY: str = ""
    
    # Ollama settings (for local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"  # or "mistral", "codellama", etc.
    
    # Which LLM to use: "openai" or "ollama"
    LLM_PROVIDER: str = "ollama"
    
    # ============================================
    # VECTOR STORE SETTINGS
    # ============================================
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    
    # Embedding model (runs locally)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # RAG settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    # ============================================
    # INDIAN LEGAL CONTEXT
    # ============================================
    DEFAULT_JURISDICTION: str = "India"
    
    # Disclaimer text to include in all AI responses
    AI_DISCLAIMER: str = (
        "⚠️ **Disclaimer**: I am an AI legal assistant, not a licensed lawyer. "
        "The information provided is for general educational purposes only and "
        "should not be considered as legal advice. For specific legal matters, "
        "please consult a qualified advocate registered with the Bar Council of India."
    )
    
    # ============================================
    # PYDANTIC SETTINGS CONFIG
    # ============================================
    model_config = SettingsConfigDict(
        # Load from .env file
        env_file=".env",
        env_file_encoding="utf-8",
        # Environment variables are case-insensitive
        case_sensitive=False,
        # Allow extra fields (for forward compatibility)
        extra="allow"
    )


# Create a global settings instance
# This is imported throughout the application
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings.
    Can be used with FastAPI's Depends() for dependency injection.
    """
    return settings