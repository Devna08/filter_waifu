"""Simple model loading and generation utilities.

The module defines minimal helpers for loading a text generation model. The
implementation falls back to a lightweight echo model when heavyweight
dependencies are unavailable.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Iterable, Optional

from .config import settings


class EchoModel:
    """A minimal stand-in model used when no backend is available."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    def generate_response(
        self, prompt: str, *, max_tokens: int, history: Optional[Iterable[str]] = None
    ) -> str:
        history_text = "\n".join(history or [])
        return (
            f"[model={self.model_id} device={settings.device}]\n"
            f"{history_text}\n{prompt}"
        ).strip()


_model: Optional[EchoModel] = None


def load_model() -> EchoModel:
    """Load and cache the text generation model.

    Returns a lightweight echo model by default. The function is structured to
    accommodate real model backends when they are added later.
    """

    global _model
    if _model is None:
        _model = EchoModel(settings.model_path)
    return _model


def generate(prompt: str, history: Optional[Iterable[str]] = None, max_tokens: Optional[int] = None) -> str:
    """Generate a completion for the provided prompt."""

    model = load_model()
    tokens = max_tokens or settings.max_tokens
    return model.generate_response(prompt, max_tokens=tokens, history=history)


async def stream_generate(
    prompt: str,
    history: Optional[Iterable[str]] = None,
    max_tokens: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Asynchronously yield generated text token-by-token.

    This implementation splits the final result into whitespace-delimited tokens
    to simulate streaming.
    """

    result = generate(prompt, history=history, max_tokens=max_tokens)
    for token in result.split():
        yield token
        await asyncio.sleep(0)
