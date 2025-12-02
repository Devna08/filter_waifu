from fastapi import FastAPI

from .model import generate
from .schemas import GenerationRequest, GenerationResponse

app = FastAPI(title="Filter Waifu Text Generation API")


@app.post("/generate", response_model=GenerationResponse)
def generate_text(request: GenerationRequest) -> GenerationResponse:
    return generate(request)
