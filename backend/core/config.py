from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "uploads"
    GEMINI_API_KEY : str
    # Server
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT:str = "development"
    # RAG settings
    RAG_TOP_K: int = 3
    RAG_SIMILARITY_THRESHOLD: float = 0.5
    EMBEDDING_DIMENSION: int = 768
    RAG_CATEGORIES: str = "formulas,examples,mistakes,constraints"

    # HITL
    HITL_CONFIDENCE_THRESHOLD: float = 0.7
    HITL_AUTO_TRIGGER_OCR: bool = True

    # Memory
    MEMORY_ENABLED: bool = True
    MEMORY_MIN_FEEDBACK_SCORE: int = 1
    MEMORY_SIMILAR_LIMIT: int = 2
    MEMORY_CACHE_TTL: int = 3600

    # Logging
    LOG_LEVEL: str = "INFO"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()