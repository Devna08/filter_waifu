from fastapi import FastAPI

from .model import generate, initialize_backend
from .schemas import GenerationRequest, GenerationResponse

app = FastAPI(title="Filter Waifu Text Generation API")


@app.on_event("startup")
def _startup() -> None:
    """Eagerly load the default backend to surface errors early."""

    initialize_backend()


@app.post("/generate", response_model=GenerationResponse)
def generate_text(request: GenerationRequest) -> GenerationResponse:
    return generate(request)
