"""Simple model loading and generation utilities.

The module defines helpers for loading a text generation model. It builds
conversation prompts from role-tagged history and supports both eager and
lazy backend initialization.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator, Iterable, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from .config import settings
from .schemas import GenerationRequest, GenerationResponse, Message

DEFAULT_BACKEND = settings.backend
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", settings.model_path)
DEFAULT_MODEL_PATH = settings.model_path

_transforms_generator = None
_transformer_tokenizer = None
_llama_instance = None
_backend_initialized = False


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


def _load_transformers_backend(model_name: str):
    global _transforms_generator, _transformer_tokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    device = 0 if torch.cuda.is_available() else -1
    _transforms_generator = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=device,
    )
    _transformer_tokenizer = tokenizer


def _load_llama_backend(model_path: str):
    global _llama_instance

    from llama_cpp import Llama

    _llama_instance = Llama(model_path=model_path)


def initialize_backend(backend: Optional[str] = None, model: Optional[str] = None):
    """Load the configured backend once.

    Parameters default to environment values but can be overridden to align with
    a runtime selection (for example, when the client passes `backend`/`model`
    on the first request).
    """

    global _backend_initialized

    if _backend_initialized:
        return

    selected_backend = (backend or DEFAULT_BACKEND).lower()
    if selected_backend == "llama":
        _load_llama_backend(model or DEFAULT_MODEL_PATH)
    else:
        _load_transformers_backend(model or DEFAULT_MODEL_NAME)

    _backend_initialized = True


def build_prompt(messages: List[Message]) -> str:
    lines = [f"{message.role}: {message.content}" for message in messages]
    return "\n".join(lines + ["assistant:"])


def _generate_with_transformers(prompt: str, request: GenerationRequest) -> str:
    if _transforms_generator is None:
        _load_transformers_backend(request.model or DEFAULT_MODEL_NAME)

    outputs = _transforms_generator(
        prompt,
        max_new_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        do_sample=True,
        eos_token_id=_transformer_tokenizer.eos_token_id if _transformer_tokenizer else None,
    )
    generated_text = outputs[0]["generated_text"]
    return generated_text[len(prompt) :].strip() if generated_text.startswith(prompt) else generated_text


def _generate_with_llama(prompt: str, request: GenerationRequest) -> str:
    if _llama_instance is None:
        _load_llama_backend(request.model or DEFAULT_MODEL_PATH)

    completion = _llama_instance.create_completion(
        prompt=prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
    )
    return completion["choices"][0]["text"].strip()


def generate_from_request(request: GenerationRequest) -> GenerationResponse:
    """Generate text from a structured request payload."""

    prompt = build_prompt(request.messages)
    backend = (request.backend or DEFAULT_BACKEND).lower()

    initialize_backend(backend=backend, model=request.model)

    if backend == "llama":
        output = _generate_with_llama(prompt, request)
    elif backend == "transformers":
        output = _generate_with_transformers(prompt, request)
    else:
        raise ValueError(f"Unsupported backend '{backend}'")

    return GenerationResponse(prompt=prompt, output=output)


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
    """Generate a completion for the provided prompt.

    This wrapper maintains compatibility with the development branch API by
    routing through the structured request generator when possible.
    """

    messages: List[Message] = [Message(role="user", content=item) for item in history or []]
    messages.append(Message(role="user", content=prompt))

    request = GenerationRequest(
        messages=messages,
        max_tokens=max_tokens or settings.max_tokens,
        temperature=settings.temperature,
        top_p=settings.top_p,
        model=None,
        backend=settings.backend,
    )
    return generate_from_request(request).output


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
