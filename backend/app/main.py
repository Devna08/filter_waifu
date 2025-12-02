from __future__ import annotations

from fastapi import FastAPI

from .config import settings
from .model import generate, initialize_backend
from .schemas import GenerationRequest, GenerationResponse

app = FastAPI(title="Filter Waifu Backend", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    """Eagerly load the default backend to surface errors early."""

    initialize_backend()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
async def config() -> dict[str, str | int | float]:
    return {
        "model_path": settings.model_path,
        "device": settings.device,
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "backend": settings.backend,
    }


@app.post("/generate", response_model=GenerationResponse)
def generate_text(request: GenerationRequest) -> GenerationResponse:
    return generate(request)
