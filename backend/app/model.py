import os
from typing import List, Optional

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


def generate(request: GenerationRequest) -> GenerationResponse:
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
