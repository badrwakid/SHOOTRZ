from __future__ import annotations
# pyright: reportMissingImports=false

import json
import logging
import time
from typing import Any, Dict, Generator, List

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.responses import StreamingResponse

from ..chat.context_builder import (
    ContextBuildOptions,
    build_user_context,
    sanitize_context_for_llm,
)
from ..contracts.chat import ChatRequest, ChatResponse
from ..services.llm import llm_service
from ..services.llm.prompt_builders import build_chat_prompt
from ..storage.db import db
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user
from .mvp import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["chat"])


def _build_system_prompt(context: Dict[str, Any]) -> str:
    return build_chat_prompt(user_context=context, messages=[])


def _build_context(payload: ChatRequest, user: AuthenticatedUser):
    return build_user_context(
        user_id=user.user_id,
        user_local_context=payload.user_local_context,
        options=ContextBuildOptions(
            include_raw_artifacts=payload.include_raw_artifacts,
            max_recent_summaries=5,
            max_chat_history=20,
        ),
    )


def _parse_chat_payload(payload_raw: Dict[str, Any]) -> ChatRequest:
    """Normalize legacy client payloads and validate once centrally.

    This avoids FastAPI-level 422s when old clients send slightly different keys
    (e.g., `userLocalContext`, `includeRawArtifacts`, or message `text`).
    """
    raw = payload_raw or {}

    raw_messages = raw.get("messages") if isinstance(raw, dict) else None
    normalized_messages: List[Dict[str, Any]] = []
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if content is None:
                content = item.get("text")
            if not isinstance(content, str):
                continue
            trimmed = content.strip()
            if not trimmed:
                continue
            normalized_messages.append({"role": role, "content": trimmed})

    normalized_payload: Dict[str, Any] = {
        "messages": normalized_messages,
        "user_local_context": raw.get("user_local_context")
        if isinstance(raw.get("user_local_context"), dict)
        else raw.get("userLocalContext"),
        "include_raw_artifacts": bool(
            raw.get("include_raw_artifacts", raw.get("includeRawArtifacts", False))
        ),
        "model": raw.get("model"),
    }

    try:
        return ChatRequest(**normalized_payload)
    except ValidationError as exc:
        logger.warning(
            "Invalid chat payload",
            extra={"errors": exc.errors(), "payload_keys": list(raw.keys()) if isinstance(raw, dict) else []},
        )
        raise HTTPException(status_code=400, detail="Invalid chat payload") from exc


# ---------------------------------------------------------------------------
# Batch endpoint
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload_raw: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    payload = _parse_chat_payload(payload_raw)
    context, context_used = _build_context(payload, user)
    context = sanitize_context_for_llm(context)
    system_prompt = _build_system_prompt(context)

    trimmed = payload.messages[-20:] if payload.messages else []
    llm_messages = [{"role": m.role, "content": m.content} for m in trimmed]

    start_ms = time.time()
    llm_resp = llm_service.chat(
        system_prompt=system_prompt,
        messages=llm_messages,
        model=payload.model,
    )
    elapsed_ms = int((time.time() - start_ms) * 1000)

    _persist_exchange(
        user_id=user.user_id,
        user_message=trimmed[-1].content if trimmed else "",
        assistant_message=llm_resp.text.strip(),
        model=llm_resp.model,
        usage=llm_resp.usage,
        elapsed_ms=elapsed_ms,
    )

    return ChatResponse(
        assistant_message=llm_resp.text.strip(),
        context_used=context_used,
        model=llm_resp.model,
        usage=llm_resp.usage,
    )


# ---------------------------------------------------------------------------
# Streaming (SSE) endpoint
# ---------------------------------------------------------------------------

def _sse_generator(
    system_prompt: str,
    messages: List[Dict[str, str]],
    context_used: Dict[str, Any],
    model: str | None,
    user_id: str,
    user_message: str,
) -> Generator[str, None, None]:
    full_response: List[str] = []
    response_model = ""
    response_usage: Dict[str, Any] | None = None
    start_ms = time.time()

    try:
        for event_type, payload in llm_service.chat_stream(
            system_prompt=system_prompt,
            messages=messages,
            model=model,
        ):
            if event_type == "delta":
                full_response.append(payload.get("text", ""))
                yield f"event: delta\ndata: {json.dumps(payload)}\n\n"
            elif event_type == "done":
                response_model = payload.get("model", "")
                response_usage = payload.get("usage")
                payload["context_used"] = context_used
                yield f"event: done\ndata: {json.dumps(payload)}\n\n"
            elif event_type == "error":
                yield f"event: error\ndata: {json.dumps(payload)}\n\n"
    except Exception as exc:
        logger.exception("Chat stream error")
        yield f"event: error\ndata: {json.dumps({'message': 'An error occurred processing your request'})}\n\n"

    elapsed_ms = int((time.time() - start_ms) * 1000)
    assistant_text = "".join(full_response).strip()
    if assistant_text:
        _persist_exchange(
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_text,
            model=response_model,
            usage=response_usage,
            elapsed_ms=elapsed_ms,
        )


@router.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload_raw: Dict[str, Any] = Body(default_factory=dict),
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    payload = _parse_chat_payload(payload_raw)
    context, context_used = _build_context(payload, user)
    context = sanitize_context_for_llm(context)
    system_prompt = _build_system_prompt(context)

    trimmed = payload.messages[-20:] if payload.messages else []
    llm_messages = [{"role": m.role, "content": m.content} for m in trimmed]
    user_message = trimmed[-1].content if trimmed else ""

    return StreamingResponse(
        _sse_generator(
            system_prompt, llm_messages, context_used,
            payload.model, user.user_id, user_message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Chat history endpoints
# ---------------------------------------------------------------------------

@router.get("/chat/history")
async def get_chat_history(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = 50,
):
    messages = db.get_chat_history(user.user_id, limit=limit)
    return {"messages": messages}


@router.delete("/chat/history")
async def clear_chat_history(
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    success = db.clear_chat_history(user.user_id)
    if success:
        return {"status": "cleared"}
    return {"status": "error", "message": "Failed to clear chat history"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _persist_exchange(
    *,
    user_id: str,
    user_message: str,
    assistant_message: str,
    model: str,
    usage: Dict[str, Any] | None,
    elapsed_ms: int,
) -> None:
    """Save both the user and assistant messages to chat_history."""
    try:
        if user_message:
            db.save_chat_message(user_id, "user", user_message)
        token_count = None
        if isinstance(usage, dict):
            token_count = usage.get("total_tokens") or usage.get("completion_tokens")
        db.save_chat_message(
            user_id, "assistant", assistant_message,
            metadata={
                "model": model,
                "tokens": token_count,
                "response_time_ms": elapsed_ms,
            },
        )
    except Exception:
        logger.exception("Failed to persist chat exchange", extra={"user_id": user_id})
