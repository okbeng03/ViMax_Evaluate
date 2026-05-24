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

    # CORS
    cors_origins: str = "*"

    # ComfyUI
    comfyui_url: str = "http://127.0.0.1:8188"
    comfyui_output_dir: str = r"D:\ComfyUI\output"
    comfyui_input_dir: str = r"D:\ComfyUI\input"
    comfyui_workflow_dir: str = "workflows"  # 本地工作流 JSON 文件目录
    comfyui_timeout: int = 1000

    # LLM
    llm_api_key: Optional[str] = None
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_model: str = "qwen3.6-27b"
    llm_timeout: int = 1000

    # Llama Server (llama.cpp)
    llama_server_path: str = "D:\llama.cpp\llama-server"  # llama.cpp server executable path
    llama_model_path: str = "D:\llama.cpp\models\qwen3.5-14b-a3b-claude-4.6-opus-reasoning-distilled-reap-q4_k_m.gguf"  # Model file path
    llama_port: int = 8080  # Server port
    llama_context_size: int = 16384  # Context window size
    llama_n_gpu_layers: int = 30  # Layers offloaded to GPU (adjust based on your VRAM)
    llama_n_threads: Optional[int] = None  # CPU threads (None = auto)
    llama_n_parallel: int = 1  # Parallel requests
    llama_flash_attention: bool = False  # Enable flash attention
    llama_startup_timeout: int = 120  # Max seconds to wait for server startup

    # CLIP
    clip_model_name: str = "ViT-L-14"  # 内置架构名称
    clip_model_path: Optional[str] = r"D:\llama.cpp\models\open_clip_pytorch_model.bin"  # 本地模型路径（可选）
    clip_device: str = "cuda"

    # Logging
    log_level: str = "INFO"

    # Performance
    max_concurrent_tasks: int = 10
    task_timeout: int = 1000


settings = Settings()
