from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .config import settings

try:
    from peft import PeftModel
except ImportError:
    PeftModel = None  # type: ignore[assignment]


_TOKENIZER = None
_MODEL = None
_DEVICE = None


def _get_device() -> torch.device:
    """설정에 따라 사용할 torch.device 선택."""
    global _DEVICE
    if _DEVICE is not None:
        return _DEVICE

    requested = settings.device.lower()
    if requested.startswith("cuda") and torch.cuda.is_available():
        _DEVICE = torch.device(requested)
    else:
        _DEVICE = torch.device("cpu")
    return _DEVICE


def _base_model_dir() -> Path:
    path = Path(settings.base_model_path)
    if not path.exists():
        raise RuntimeError(f"Base model path does not exist: {path}")
    return path

def _adapter_dir() -> Path:
    path = Path(settings.adapter_path)
    if not path.exists():
        raise RuntimeError(f"Adapter path does not exist: {path}")
    return path


def load_model() -> Tuple[AutoTokenizer, torch.nn.Module]:
    """Mistral + (옵션) LoRA 어댑터를 로드하고 캐시."""
    global _TOKENIZER, _MODEL
    if _TOKENIZER is not None and _MODEL is not None:
        return _TOKENIZER, _MODEL

    base_dir = _base_model_dir()
    device = _get_device()

    # ✅ 여기서 읽는 config.json 이 바로 Mistral-7B-v0.2 의 config 여야 함
    tokenizer = AutoTokenizer.from_pretrained(base_dir, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    torch_dtype = torch.float16 if device.type == "cuda" else torch.float32

    base_model = AutoModelForCausalLM.from_pretrained(
        base_dir,
        torch_dtype=torch_dtype,
        device_map=None,
    ).to(device)

    model = base_model
    if PeftModel is not None:
        try:
            adapter_dir = _adapter_dir()
            model = PeftModel.from_pretrained(base_model, adapter_dir)
        except Exception:
            # 어댑터 로드에 실패하면 베이스 모델만 사용
            model = base_model

    model.eval()
    _TOKENIZER = tokenizer
    _MODEL = model
    return _TOKENIZER, _MODEL


def classify_text(text: str) -> Dict[str, object]:
    """입력 문장을 SAFE / UNSAFE 로 분류."""
    tokenizer, model = load_model()
    device = _get_device()

    instruction = (
        "다음 사용자의 발화가 부적절한 표현인지 판별하십시오. "
        "부적절한 경우에는 'UNSAFE', 문제가 없으면 'SAFE' 라는 단어 하나만 출력하세요.\n\n"
        f"사용자: {text}\n"
        "판단:"
    )

    inputs = tokenizer(
        instruction,
        return_tensors="pt",
        truncation=True,
        max_length=settings.max_tokens,
    ).to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=4,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0][inputs["input_ids"].shape[1]:]
    generated_text = tokenizer.decode(
        generated_ids, skip_special_tokens=True
    ).strip()

    normalized = generated_text.upper()

    label_keywords = {
        "safe": ["SAFE", "OK"],
        "unsafe": ["UNSAFE", "NOT SAFE", "BAD"],
    }

    is_safe: Optional[bool] = None
    if any(kw in normalized for kw in label_keywords["unsafe"]):
        is_safe = False
    elif any(kw in normalized for kw in label_keywords["safe"]):
        is_safe = True

    if is_safe is None:
        # 애매하면 보수적으로 unsafe 처리
        is_safe = False

    return {
        "is_safe": is_safe,
        "raw_decision": generated_text,
        "normalized_decision": normalized,
    }
