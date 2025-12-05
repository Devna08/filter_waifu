from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat

from .config import settings
from .routes.chat import router as chat_router

app = FastAPI(title="Filter Waifu Backend", version="0.1.0")

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],      # GET, POST, OPTIONS 등 모두 허용
    allow_headers=["*"],      # Content-Type 등 모든 헤더 허용
)

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
    }


app.include_router(chat_router)
