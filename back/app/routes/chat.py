from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from ..model import classify_text

router = APIRouter(prefix="/api", tags=["chat"])


class Message(BaseModel):
    role: str = Field(..., description="Message author role, e.g., user or assistant.")
    content: str = Field(..., description="Message content.")

    @validator("role")
    def validate_role(cls, value: str) -> str:  # noqa: D417
        allowed = {"user", "assistant", "system"}
        if value not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return value


class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = Field(
        None, ge=1, description="Optional override for token limit (현재는 사용하지 않음)."
    )


class ChatResponse(BaseModel):
    role: str = Field("assistant", description="Role of the generated message")
    content: str
    is_safe: Optional[bool] = Field(
        None, description="True if the last user message is considered safe."
    )
    raw_decision: Optional[str] = Field(
        None, description="Raw classifier output text (for debugging)."
    )


def _get_last_user_message(messages: List[Message]) -> Message:
    """가장 마지막 user 역할 메시지를 찾는다."""
    for message in reversed(messages):
        if message.role == "user":
            return message
    raise ValueError("At least one user message is required.")


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    try:
        last_user_message = _get_last_user_message(request.messages)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # 필터 모델로 분류 수행
    result = classify_text(last_user_message.content)
    is_safe: bool = bool(result.get("is_safe"))
    raw_decision: str = str(result.get("raw_decision", ""))

    if is_safe:
        reply_text = "이 메시지는 필터 기준으로 안전한 표현으로 판단되었습니다."
    else:
        reply_text = "부적절한 표현이 감지되어 메시지가 차단되었습니다."

    return ChatResponse(
        content=reply_text,
        is_safe=is_safe,
        raw_decision=raw_decision,
    )
