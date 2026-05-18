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
    comfyui_output_dir: str = r"D:\ComfyUI\output"
    comfyui_workflow_dir: str = "workflows"  # 本地工作流 JSON 文件目录
    comfyui_timeout: int = 300

    # LLM
    llm_api_key: Optional[str] = None
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_model: str = "gpt-4o"
    llm_timeout: int = 120

    # CLIP
    clip_model_name: str = "apple/DFN2B-CLIP-ViT-L-14-39B"
    clip_model_path: Optional[str] = r"D:\llama.cpp\models\open_clip_pytorch_model.bin"  # 本地模型路径，如 ~/.cache/huggingface/hub/open_clip_pytorch_model.bin
    clip_device: str = "cuda"

    # Logging
    log_level: str = "INFO"

    # Performance
    max_concurrent_tasks: int = 10
    task_timeout: int = 1000


settings = Settings()
