"""Configuration management using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Agent图像评估系统"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///data/evaluations.db"

    # API
    api_v1_prefix: str = "/api/v1"

    # ComfyUI
    comfyui_url: str = "http://localhost:8188"
    comfyui_timeout: int = 300

    # LLM
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_timeout: int = 120

    # CLIP
    clip_model_name: str = "apple/DFN2B-CLIP-ViT-L-14-39B"
    clip_device: str = "cuda"

    # Logging
    log_level: str = "INFO"

    # Performance
    max_concurrent_tasks: int = 10
    task_timeout: int = 300


settings = Settings()
