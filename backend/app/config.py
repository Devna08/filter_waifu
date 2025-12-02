"""Application configuration settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    model_path: str = Field("sshleifer/tiny-gpt2", env="MODEL_PATH")
    device: str = Field("cpu", env="DEVICE")
    max_tokens: int = Field(128, env="MAX_TOKENS")
    temperature: float = Field(0.7, env="TEMPERATURE")
    top_p: float = Field(0.9, env="TOP_P")
    backend: Literal["transformers", "llama"] = Field("transformers", env="MODEL_BACKEND")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
