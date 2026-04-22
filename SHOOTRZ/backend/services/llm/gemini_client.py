"""Gemini 2.5 Flash client using the official google-genai SDK.

Provides batch, structured-JSON, and streaming generation through a single
``GeminiService`` class with built-in retry, timeout, and error mapping.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Tuple, Type

from pydantic import BaseModel

from ...utils import config

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.5-flash"
_DEFAULT_TEMPERATURE = 0.4
_MAX_RETRIES = 3
_BASE_TIMEOUT = 60


@dataclass(frozen=True)
class LlmResponse:
    text: str
    model: str
    usage: Optional[Dict[str, Any]] = None


def _get_api_key() -> str:
    key = (config.GEMINI_API_KEY or "").strip()
    placeholder = {"your_gemini_api_key_here", "changeme", ""}
    if not key or key.lower() in placeholder:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini API key missing. Set GEMINI_API_KEY in backend/.env "
                "(get a key at https://aistudio.google.com/apikey) and restart."
            ),
        )
    return key


def _get_model() -> str:
    return getattr(config, "GEMINI_MODEL", None) or _DEFAULT_MODEL


def _get_max_retries() -> int:
    return int(getattr(config, "GEMINI_MAX_RETRIES", _MAX_RETRIES))


def _get_timeout() -> int:
    return int(getattr(config, "GEMINI_TIMEOUT", _BASE_TIMEOUT))


def _extract_usage(response: Any) -> Optional[Dict[str, Any]]:
    um = getattr(response, "usage_metadata", None)
    if um is None:
        return None
    return {
        "prompt_tokens": getattr(um, "prompt_token_count", None),
        "completion_tokens": getattr(um, "candidates_token_count", None),
        "total_tokens": getattr(um, "total_token_count", None),
    }


def _map_error(exc: Exception) -> Tuple[int, str]:
    """Map google-genai / API exceptions to (http_status, message)."""
    msg = str(exc)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        return (
            429,
            "Gemini rate limit reached. Wait 1-2 minutes and try again, "
            "or enable billing for higher quotas.",
        )
    if "403" in msg or "PERMISSION_DENIED" in msg:
        return 403, "Gemini API rejected the request. Check API key and permissions."
    if "400" in msg or "INVALID_ARGUMENT" in msg:
        return 400, f"Gemini rejected the request: {msg[:300]}"
    return 502, f"Gemini API error: {msg[:300]}"


class GeminiService:
    """Thin wrapper around the ``google.genai`` SDK for Gemini 2.5 Flash."""

    def __init__(self) -> None:
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=_get_api_key())
        return self._client

    def _build_contents(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> Tuple[Any, List[Any]]:
        """Return (system_instruction, contents) for the SDK."""
        from google.genai import types

        contents: list = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            ))
        return system_prompt, contents

    # ------------------------------------------------------------------
    # Batch (non-streaming) free-text generation
    # ------------------------------------------------------------------

    def generate(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = _DEFAULT_TEMPERATURE,
    ) -> LlmResponse:
        from google.genai import types

        client = self._ensure_client()
        model_name = model or _get_model()
        system_instruction, contents = self._build_contents(system_prompt, messages)
        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )

        response = self._call_with_retry(
            lambda: client.models.generate_content(
                model=model_name,
                contents=contents,
                config=gen_config,
            )
        )

        text = response.text or ""
        return LlmResponse(text=text, model=model_name, usage=_extract_usage(response))

    # ------------------------------------------------------------------
    # Structured JSON generation with Pydantic schema
    # ------------------------------------------------------------------

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: Type[BaseModel],
        model: Optional[str] = None,
        temperature: float = _DEFAULT_TEMPERATURE,
    ) -> Any:
        """Generate a response constrained to a Pydantic JSON schema.

        Returns a parsed Pydantic model instance, or raises on failure.
        """
        from google.genai import types

        client = self._ensure_client()
        model_name = model or _get_model()

        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )

        response = self._call_with_retry(
            lambda: client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=gen_config,
            )
        )

        import json
        raw_text = response.text or ""
        data = json.loads(raw_text)
        return schema.model_validate(data)

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------

    def stream(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = _DEFAULT_TEMPERATURE,
    ) -> Generator[Tuple[str, Any], None, None]:
        """Yields ``("delta", {"text": ...})``, then ``("done", {...})``."""
        from google.genai import types

        client = self._ensure_client()
        model_name = model or _get_model()
        system_instruction, contents = self._build_contents(system_prompt, messages)
        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )

        usage: Optional[Dict[str, Any]] = None
        try:
            stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=gen_config,
            )
            for chunk in stream:
                text = chunk.text
                if text:
                    yield ("delta", {"text": text})
                chunk_usage = _extract_usage(chunk)
                if chunk_usage:
                    usage = chunk_usage

            yield ("done", {"model": model_name, "usage": usage})
        except Exception as exc:
            code, detail = _map_error(exc)
            logger.error("Gemini stream error: %s", detail, exc_info=True)
            yield ("error", {"message": detail, "status_code": code})

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    def _call_with_retry(self, fn: Any) -> Any:
        max_retries = _get_max_retries()
        timeout_s = _get_timeout()
        last_exc: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as exc:
                last_exc = exc
                code, detail = _map_error(exc)
                if code == 429:
                    wait = min(2 ** attempt * 2, 30)
                    logger.warning(
                        "Gemini rate-limited (attempt %d/%d), retrying in %ds",
                        attempt + 1, max_retries, wait,
                    )
                    time.sleep(wait)
                    continue
                if code >= 500:
                    wait = 2 ** attempt
                    logger.warning(
                        "Gemini server error (attempt %d/%d), retrying in %ds",
                        attempt + 1, max_retries, wait,
                    )
                    time.sleep(wait)
                    continue
                raise

        from fastapi import HTTPException
        code, detail = _map_error(last_exc) if last_exc else (502, "Gemini unreachable")
        raise HTTPException(status_code=code, detail=detail)


gemini_service = GeminiService()
