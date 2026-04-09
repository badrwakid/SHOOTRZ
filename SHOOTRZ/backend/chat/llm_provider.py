"""Thin abstraction that delegates to the configured LLM backend.

Reads ``LLM_PROVIDER`` from ``config`` (default ``"gemini"``).
Supported values: ``"gemini"``, ``"openai"``.
"""

from __future__ import annotations

from typing import Any, Dict, Generator, List, Optional, Tuple

from ..utils import config
from .openai_client import LlmResponse


def _provider() -> str:
    return (getattr(config, "LLM_PROVIDER", None) or "gemini").lower().strip()


def generate(
    *,
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> LlmResponse:
    """Batch (non-streaming) completion via the active provider."""
    provider = _provider()

    if provider == "openai":
        from .openai_client import generate_chat_completion
        return generate_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            model=model,
        )

    from .gemini_client import generate_chat_completion
    return generate_chat_completion(
        system_prompt=system_prompt,
        messages=messages,
        model=model,
    )


def stream(
    *,
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> Generator[Tuple[str, Any], None, None]:
    """Streaming completion via the active provider.

    Yields ``(event_type, payload)`` tuples — see ``gemini_client`` for the
    event contract.  OpenAI streaming is not implemented yet; calling it
    falls back to a single-shot batch wrapped as a ``delta`` + ``done`` pair.
    """
    provider = _provider()

    if provider == "openai":
        from .openai_client import generate_chat_completion
        resp = generate_chat_completion(
            system_prompt=system_prompt,
            messages=messages,
            model=model,
        )
        yield ("delta", {"text": resp.text})
        yield ("done", {"model": resp.model, "usage": resp.usage})
        return

    from .gemini_client import stream_chat_completion
    yield from stream_chat_completion(
        system_prompt=system_prompt,
        messages=messages,
        model=model,
    )
