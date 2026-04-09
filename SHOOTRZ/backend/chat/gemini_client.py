"""Gemini LLM client using the REST API directly (no SDK needed).

Only depends on ``requests`` which is already in the project.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Generator, List, Optional, Tuple

import requests
from fastapi import HTTPException

from ..utils import config
from .openai_client import LlmResponse

_DEFAULT_MODEL = "gemini-2.0-flash"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _get_api_key() -> str:
    key = (config.GEMINI_API_KEY or "").strip()
    placeholder = {"your_gemini_api_key_here", "changeme", ""}
    if not key or key.lower() in placeholder:
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini API key missing. Set GEMINI_API_KEY in SHOOTRZ/backend/.env "
                "(get a key at https://aistudio.google.com/apikey) and restart the API "
                "server. If the key is already set, remove any empty GEMINI_API_KEY from "
                "your system environment so backend/.env can apply."
            ),
        )
    return key


def _chosen_model(model: Optional[str] = None) -> str:
    return model or getattr(config, "GEMINI_MODEL", None) or _DEFAULT_MODEL


def _to_gemini_body(
    system_prompt: str,
    messages: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Build the Gemini request body from OpenAI-style messages."""
    contents: list = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    return {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4},
    }


def _extract_usage(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    um = data.get("usageMetadata")
    if not um:
        return None
    return {
        "prompt_tokens": um.get("promptTokenCount"),
        "completion_tokens": um.get("candidatesTokenCount"),
        "total_tokens": um.get("totalTokenCount"),
    }


def _extract_text(data: Dict[str, Any]) -> str:
    """Pull the assistant text out of a Gemini response object."""
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""


def _format_gemini_http_error(status_code: int, body: str) -> Tuple[int, str]:
    """Map Gemini HTTP errors to a short user-facing message and client status."""
    api_msg: Optional[str] = None
    try:
        data = json.loads(body)
        api_msg = (data.get("error") or {}).get("message")
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    if status_code == 429:
        return (
            429,
            (
                "Gemini free-tier limit reached (too many requests or tokens per minute/day). "
                "Wait 1–2 minutes and try again, or try again tomorrow. "
                "See https://ai.google.dev/gemini-api/docs/rate-limits — "
                "optional: enable billing in Google AI Studio for higher quotas."
            ),
        )

    if status_code == 403:
        return (
            403,
            api_msg
            or "Gemini API rejected the request. Check the API key and that the Generative Language API is enabled.",
        )

    if api_msg:
        return (502, f"Gemini error ({status_code}): {api_msg[:400]}")

    return (502, f"Gemini API error ({status_code}).")


# ---------------------------------------------------------------------------
# Batch (non-streaming) completion
# ---------------------------------------------------------------------------

def generate_chat_completion(
    *,
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> LlmResponse:
    api_key = _get_api_key()
    model_name = _chosen_model(model)
    # BUG FIX: Move API key from URL query string to header to prevent leaking in logs
    url = f"{_BASE_URL}/models/{model_name}:generateContent"

    try:
        resp = requests.post(
            url,
            json=_to_gemini_body(system_prompt, messages),
            headers={"x-goog-api-key": api_key},
            timeout=60,
        )

        if resp.status_code != 200:
            code, detail = _format_gemini_http_error(resp.status_code, resp.text)
            raise HTTPException(status_code=code, detail=detail)

        data = resp.json()
        text = _extract_text(data)
        usage = _extract_usage(data)
        return LlmResponse(text=text, model=model_name, usage=usage)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Gemini provider error") from exc


# ---------------------------------------------------------------------------
# Streaming completion — yields (event_type, data) tuples
# ---------------------------------------------------------------------------

def stream_chat_completion(
    *,
    system_prompt: str,
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
) -> Generator[Tuple[str, Any], None, None]:
    """Synchronous generator that yields ``("delta", {"text": ...})`` tuples
    followed by a final ``("done", {"model": ..., "usage": ...})`` tuple.

    Uses the Gemini ``streamGenerateContent?alt=sse`` endpoint.
    """
    api_key = _get_api_key()
    model_name = _chosen_model(model)
    # BUG FIX: Move API key from URL query string to header to prevent leaking in logs
    url = f"{_BASE_URL}/models/{model_name}:streamGenerateContent?alt=sse"

    usage: Optional[Dict[str, Any]] = None

    try:
        resp = requests.post(
            url,
            json=_to_gemini_body(system_prompt, messages),
            headers={"x-goog-api-key": api_key},
            timeout=120,
            stream=True,
        )

        if resp.status_code != 200:
            _, detail = _format_gemini_http_error(resp.status_code, resp.text)
            yield ("error", {"message": detail})
            return

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if not line.startswith("data: "):
                continue

            raw_json = line[len("data: "):]
            try:
                chunk = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            text = _extract_text(chunk)
            if text:
                yield ("delta", {"text": text})

            chunk_usage = _extract_usage(chunk)
            if chunk_usage:
                usage = chunk_usage

        yield ("done", {"model": model_name, "usage": usage})

    except HTTPException:
        raise
    except Exception as exc:
        yield ("error", {"message": str(exc)})
