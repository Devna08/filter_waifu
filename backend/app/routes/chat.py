from fastapi import APIRouter

from ..model import generate_from_request
from ..schemas import GenerationRequest, GenerationResponse

router = APIRouter()


@router.post("/generate", response_model=GenerationResponse)
def generate_text(request: GenerationRequest) -> GenerationResponse:
    return generate_from_request(request)
