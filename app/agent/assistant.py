"""
Dual LangGraph agent definitions — Jisr AI Assistants.

Two agents with different access levels:
1. HR Agent     — full access to all employee data, reports, payroll
2. Employee Agent — scoped to one employee's own data only
"""

from __future__ import annotations

import os
from typing import Any
from typing import AsyncIterator

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import HR_ADMIN_PROMPT, EMPLOYEE_PROMPT
from app.agent.tools import HR_TOOLS, EMPLOYEE_TOOLS

load_dotenv()

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

# ──────────────────────────────────────────────
# In-memory session store
# ──────────────────────────────────────────────
_session_histories: dict[str, list] = {}


def _get_history(session_id: str) -> list:
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    return _session_histories[session_id]


def clear_history(session_id: str) -> None:
    """Clear chat history for a given session."""
    _session_histories.pop(session_id, None)


def _extract_text(content: Any) -> str:
    """Normalize AIMessage.content to a plain string.

    Gemini may return content as:
    - str: "hello"
    - list: [{'type': 'text', 'text': 'hello'}]
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


# ──────────────────────────────────────────────
# Shared LLM instance
# ──────────────────────────────────────────────
_llm = ChatGoogleGenerativeAI(
    model=_MODEL,
    temperature=_TEMPERATURE,
    streaming=True,
)

# ──────────────────────────────────────────────
# Agent 1 — HR / Admin (full access)
# ──────────────────────────────────────────────
_hr_agent = create_react_agent(
    model=_llm,
    tools=HR_TOOLS,
    prompt=HR_ADMIN_PROMPT,
)

# ──────────────────────────────────────────────
# Agent 2 — Employee Self-Service (scoped)
# ──────────────────────────────────────────────
_employee_agent = create_react_agent(
    model=_llm,
    tools=EMPLOYEE_TOOLS,
    prompt=EMPLOYEE_PROMPT,
)


def _get_agent(agent_type: str):
    """Return the correct agent based on type."""
    if agent_type == "employee":
        return _employee_agent
    return _hr_agent


# ──────────────────────────────────────────────
# Non-streaming chat
# ──────────────────────────────────────────────
async def chat(
    user_message: str,
    session_id: str = "default",
    agent_type: str = "hr",
    employee_id: str | None = None,
) -> str:
    """
    Send a message and get a complete response.

    Args:
        user_message: The user's input text.
        session_id:   Unique session ID for history isolation.
        agent_type:   "hr" for admin agent, "employee" for self-service.
        employee_id:  Employee ID for self-service agent (e.g. "EMP-001").
    """
    history = _get_history(session_id)
    agent = _get_agent(agent_type)

    # For employee agent, inject the employee_id context
    message = user_message
    if agent_type == "employee" and employee_id:
        message = f"[معرّف الموظف الحالي: {employee_id}]\n\n{user_message}"

    messages = history + [HumanMessage(content=message)]
    result = await agent.ainvoke({"messages": messages})

    ai_messages = [
        m for m in result.get("messages", [])
        if isinstance(m, AIMessage) and m.content and not m.tool_calls
    ]
    output = _extract_text(ai_messages[-1].content) if ai_messages else ""

    # Store original user message (without injected context) in history
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=output))

    return output


# ──────────────────────────────────────────────
# Streaming chat (SSE)
# ──────────────────────────────────────────────
async def chat_stream(
    user_message: str,
    session_id: str = "default",
    agent_type: str = "hr",
    employee_id: str | None = None,
) -> AsyncIterator[str]:
    """Stream the agent response token-by-token."""
    history = _get_history(session_id)
    agent = _get_agent(agent_type)

    message = user_message
    if agent_type == "employee" and employee_id:
        message = f"[معرّف الموظف الحالي: {employee_id}]\n\n{user_message}"

    messages = history + [HumanMessage(content=message)]
    full_response = ""

    async for event in agent.astream_events(
        {"messages": messages},
        version="v2",
    ):
        if event.get("event") == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                text = _extract_text(chunk.content)
                if text:
                    full_response += text
                    yield text

    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=full_response))
