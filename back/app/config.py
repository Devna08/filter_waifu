from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"


class Settings(BaseSettings):
    """Application configuration."""

    # Mistral-7B v0.2 기본 모델이 들어 있는 폴더 (models/base)
    base_model_path: str = Field(
        default=str(MODELS_DIR / "base"),
        description="Path to base Mistral-7B-v0.2 model directory.",
    )

    # LoRA / 어댑터가 들어 있는 폴더 (models/adapter)
    adapter_path: str = Field(
        default=str(MODELS_DIR / "adapter"),
        description="Path to LoRA/adapter directory.",
    )

    device: str = Field(
        default="cpu",
        description="Target device for model execution. e.g. 'cpu', 'cuda', 'cuda:0'",
    )

    max_tokens: int = Field(
        default=256,
        description="Maximum tokens for prompt length.",
    )

    temperature: float = Field(
        default=0.7,
        description="Sampling temperature for generation (if used).",
    )

    class Config:
        env_file = ".env"


def get_settings() -> "Settings":
    return Settings()


settings = get_settings()
