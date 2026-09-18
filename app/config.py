"""Centralized environment-based application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_path: Path = Path("data/local_ai_documenter.db")
    upload_dir: Path = Path("data/uploads")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "local-ai-documenter"
    pinecone_namespace: str = "documents"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    ollama_model: str = "qwen3:8b"
    ollama_base_url: str = "http://localhost:11434"
    chunk_size: int = Field(default=1000, ge=100)
    chunk_overlap: int = Field(default=150, ge=0)
    top_k: int = Field(default=5, ge=1, le=50)
    retrieval_min_score: float | None = Field(default=None, ge=-1, le=1)
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    api_base_url: str = "http://localhost:8000"
    auth_session_days: int = Field(default=7, ge=1, le=90)
    auth_cookie_secure: bool = False

    @model_validator(mode="after")
    def validate_chunking(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one reusable settings instance."""

    return Settings()
