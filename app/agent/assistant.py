"""
LangChain 0.3 agent definition — Jisr AI Assistant.

Uses create_tool_calling_agent with ChatGoogleGenerativeAI (Gemini 2.5 Flash)
and maintains per-session chat history for multi-turn conversations.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from app.agent.prompts import JISR_AI_SYSTEM_PROMPT
from app.agent.tools import ALL_TOOLS

load_dotenv()

_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

_session_histories: dict[str, list] = {}


def _get_history(session_id: str) -> list:
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    return _session_histories[session_id]


_llm = ChatGoogleGenerativeAI(
    model=_MODEL,
    temperature=_TEMPERATURE,
    streaming=True,
    convert_system_message_to_human=False,
)

_prompt = ChatPromptTemplate.from_messages([
    ("system", JISR_AI_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

_agent = create_tool_calling_agent(llm=_llm, tools=ALL_TOOLS, prompt=_prompt)

_agent_executor = AgentExecutor(
    agent=_agent,
    tools=ALL_TOOLS,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10,
    return_intermediate_steps=False,
)


async def chat(user_message: str, session_id: str = "default") -> str:
    """Send a message and get a complete response."""
    history = _get_history(session_id)
    result = await _agent_executor.ainvoke(
        {"input": user_message, "chat_history": history}
    )
    output = result.get("output", "")
    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=output))
    return output


async def chat_stream(
    user_message: str, session_id: str = "default"
) -> AsyncIterator[str]:
    """Stream the agent response token-by-token via astream_events v2."""
    history = _get_history(session_id)
    full_response = ""

    async for event in _agent_executor.astream_events(
        {"input": user_message, "chat_history": history},
        version="v2",
    ):
        if event.get("event") == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                if isinstance(chunk.content, str):
                    full_response += chunk.content
                    yield chunk.content

    history.append(HumanMessage(content=user_message))
    history.append(AIMessage(content=full_response))
