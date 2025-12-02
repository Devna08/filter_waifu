from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, validator

from ..model import generate, stream_generate

router = APIRouter(prefix="/api", tags=["chat"])


class Message(BaseModel):
    role: str = Field(..., description="Message author role, e.g., user or assistant.")
    content: str = Field(..., description="Message content.")

    @validator("role")
    def validate_role(cls, value: str) -> str:  # noqa: D417 - Pydantic validator signature
        allowed = {"user", "assistant", "system"}
        if value not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return value


class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = Field(None, ge=1, description="Optional override for token limit.")


class ChatResponse(BaseModel):
    role: str = Field("assistant", description="Role of the generated message")
    content: str


def _format_prompt(messages: List[Message]) -> str:
    return "\n".join(f"{message.role}: {message.content}" for message in messages)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    prompt = _format_prompt(request.messages)
    history = [f"{message.role}: {message.content}" for message in request.messages[:-1]]
    completion = generate(prompt, history=history, max_tokens=request.max_tokens)
    return ChatResponse(content=completion)


@router.websocket("/ws/chat")
async def chat_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                messages_payload = payload.get("messages", [])
                messages = [Message(**message) for message in messages_payload]
                max_tokens = payload.get("max_tokens")
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                await websocket.send_text(f"Invalid payload: {exc}")
                continue

            if not messages:
                await websocket.send_text("messages must not be empty")
                continue

            prompt = _format_prompt(messages)
            history = [f"{message.role}: {message.content}" for message in messages[:-1]]
            async for token in stream_generate(prompt, history=history, max_tokens=max_tokens):
                await websocket.send_text(token)
            await websocket.send_text("[DONE]")
    except WebSocketDisconnect:
        return
