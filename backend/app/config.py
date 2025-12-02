from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables when available."""

    model_path: str = Field(
        default="models/llm",
        description="Path to the local model or identifier for remote loading.",
    )
    device: str = Field(default="cpu", description="Target device for model execution.")
    max_tokens: int = Field(default=256, description="Default maximum tokens for generation.")
    temperature: float = Field(default=0.7, description="Sampling temperature for text generation.")

    class Config:
        env_file = ".env"


def get_settings() -> "Settings":
    """Return a shared settings instance."""

    return Settings()


settings = get_settings()
