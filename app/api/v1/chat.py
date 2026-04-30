"""
Chat API — v1 endpoints for both HR and Employee agents.

Provides:
- POST /api/v1/chat/          — Non-streaming chat
- POST /api/v1/chat/stream    — SSE streaming chat

Both endpoints accept an `agent_type` field ("hr" or "employee")
to route to the correct agent.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agent.assistant import chat, chat_stream

router = APIRouter(prefix="/chat", tags=["Chat"])


# ──────────────────────────────────────────────
# Enums & Schemas
# ──────────────────────────────────────────────
class AgentType(str, Enum):
    HR = "hr"
    EMPLOYEE = "employee"


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's message to the AI assistant.",
        examples=["ما هو إجمالي الرواتب لهذا الشهر؟"],
    )
    session_id: Optional[str] = Field(
        default="default",
        description="Unique session ID for conversation continuity.",
        examples=["sess_abc123"],
    )
    agent_type: AgentType = Field(
        default=AgentType.HR,
        description="Which agent to use: 'hr' for admin or 'employee' for self-service.",
    )
    employee_id: Optional[str] = Field(
        default=None,
        description="Employee ID for self-service agent (e.g. 'EMP-001'). Required when agent_type is 'employee'.",
        examples=["EMP-001"],
    )


class ChatResponse(BaseModel):
    """Non-streaming response."""

    reply: str
    session_id: str
    agent_type: str


# ──────────────────────────────────────────────
# POST /api/v1/chat  — non-streaming
# ──────────────────────────────────────────────
@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a message (non-streaming)",
    description="Send a message to either the HR or Employee agent.",
)
async def chat_endpoint(req: ChatRequest):
    if req.agent_type == AgentType.EMPLOYEE and not req.employee_id:
        raise HTTPException(
            status_code=400,
            detail="employee_id is required when agent_type is 'employee'",
        )
    try:
        reply = await chat(
            req.message,
            session_id=req.session_id,
            agent_type=req.agent_type.value,
            employee_id=req.employee_id,
        )
        return ChatResponse(
            reply=reply,
            session_id=req.session_id,
            agent_type=req.agent_type.value,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# POST /api/v1/chat/stream  — SSE streaming
# ──────────────────────────────────────────────
@router.post(
    "/stream",
    summary="Send a message (streaming via SSE)",
    description="Send a message and receive a real-time token stream from either agent.",
)
async def chat_stream_endpoint(req: ChatRequest):
    if req.agent_type == AgentType.EMPLOYEE and not req.employee_id:
        raise HTTPException(
            status_code=400,
            detail="employee_id is required when agent_type is 'employee'",
        )

    async def event_generator():
        try:
            async for token in chat_stream(
                req.message,
                session_id=req.session_id,
                agent_type=req.agent_type.value,
                employee_id=req.employee_id,
            ):
                yield {
                    "event": "token",
                    "data": json.dumps({"content": token}, ensure_ascii=False),
                }
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
