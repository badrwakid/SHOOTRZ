from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list)
    user_local_context: Optional[Dict[str, Any]] = None
    include_raw_artifacts: bool = False
    model: Optional[str] = None


class ChatResponse(BaseModel):
    assistant_message: str
    context_used: Dict[str, Any]
    model: str
    usage: Optional[Dict[str, Any]] = None
