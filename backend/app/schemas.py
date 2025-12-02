from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .config import settings


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class GenerationRequest(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    max_tokens: int = Field(
        settings.max_tokens, description="Maximum number of new tokens to generate"
    )
    temperature: float = Field(settings.temperature, description="Sampling temperature")
    top_p: float = Field(settings.top_p, description="Top-p nucleus sampling")
    model: Optional[str] = Field(
        default=None, description="Optional model name or path override for generation",
    )
    backend: Optional[Literal["transformers", "llama"]] = Field(
        default=None, description="Optional backend selector",
    )

    class Config:
        allow_population_by_field_name = True


class GenerationResponse(BaseModel):
    prompt: str
    output: str
