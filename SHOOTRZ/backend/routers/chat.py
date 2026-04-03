from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from ..chat.context_builder import ContextBuildOptions, build_user_context
from ..chat.openai_client import generate_chat_completion
from ..contracts.chat import ChatRequest, ChatResponse
from ..utils.supabase_auth import get_authenticated_user


router = APIRouter(prefix="", tags=["chat"])


def _build_system_prompt(context: Dict[str, Any]) -> str:
    # Keep this deterministic and explicit: coach persona + how to use data.
    # Important: keep it short enough to not balloon tokens.
    context_json = json.dumps(context, ensure_ascii=False)
    return (
        "You are Coach J, an elite basketball shooting coach inside the SHOOTRZ app.\n"
        "You MUST personalize advice using the user's data below.\n"
        "Rules:\n"
        "- Be concise and actionable. Prefer bullet points.\n"
        "- If the user asks about progress, reference trends from history.\n"
        "- If data is missing, ask 1 clarifying question.\n"
        "- Never invent specific numbers not present in the data.\n"
        "- When suggesting drills, give sets/reps and a 7-day plan.\n"
        "\n"
        "USER_DATA_JSON:\n"
        f"{context_json}\n"
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user=Depends(get_authenticated_user),
):
    # Build full context (server + client local)
    context, context_used = build_user_context(
        user_id=user.user_id,
        user_local_context=payload.user_local_context,
        options=ContextBuildOptions(
            include_raw_artifacts=payload.include_raw_artifacts,
            max_videos=8,
            max_metrics_per_video=25,
        ),
    )

    system_prompt = _build_system_prompt(context)

    # Only pass a bounded number of messages to the model
    trimmed = payload.messages[-20:] if payload.messages else []
    llm_messages = [{"role": m.role, "content": m.content} for m in trimmed]

    llm_resp = generate_chat_completion(
        system_prompt=system_prompt,
        messages=llm_messages,
        model=payload.model,
    )

    return ChatResponse(
        assistant_message=llm_resp.text.strip(),
        context_used=context_used,
        model=llm_resp.model,
        usage=llm_resp.usage,
    )



