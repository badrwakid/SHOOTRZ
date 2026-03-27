from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from ..utils import config


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str
    usage: Optional[Dict[str, Any]] = None


def generate_chat_completion(
    *,
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> LlmResponse:
    """
    Calls OpenAI Chat Completions and returns assistant text.

    Expected `messages` format:
      [{"role": "user"|"assistant", "content": "..."}]
    """
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the server")

    try:
        # openai>=1.0.0
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=config.OPENAI_API_KEY)
        chosen_model = model or config.OPENAI_MODEL

        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=0.4,
        )

        text = resp.choices[0].message.content or ""
        usage = None
        if getattr(resp, "usage", None) is not None:
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
                "completion_tokens": getattr(resp.usage, "completion_tokens", None),
                "total_tokens": getattr(resp.usage, "total_tokens", None),
            }
        return LlmResponse(text=text, model=chosen_model, usage=usage)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="LLM provider error") from exc




