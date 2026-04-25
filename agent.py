"""
The agent loop: Think -> Act -> Observe -> Repeat.

This is the heart of "Agentic Engineering". Instead of one LLM call,
we run a loop where the LLM can keep calling tools until it has enough
information to answer the user.
"""
from __future__ import annotations

import json
import os
import ssl
from typing import Any, Iterator

import httpx
import truststore
from openai import OpenAI

from tools import TOOL_FUNCTIONS, TOOLS_SCHEMA

SYSTEM_PROMPT = """You are a helpful, concise Smart Task Assistant.
You have access to tools for time, math, weather, and a to-do list.
Use tools when they help. After tool calls, summarize results for the user
in plain language. If a question is unrelated to your tools, just answer normally."""

MAX_STEPS = 6  # safety guardrail to prevent infinite tool loops


def _client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env.")
    # Use the Windows certificate store so corporate SSL-inspection proxies work.
    ssl_ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    http_client = httpx.Client(verify=ssl_ctx)
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=key, base_url=base_url, http_client=http_client)
    return OpenAI(api_key=key, http_client=http_client)


def run_agent(
    user_message: str, history: list[dict[str, Any]]
) -> Iterator[dict[str, Any]]:
    """
    Run one turn of the agent. Yields trace events so the UI can show progress:
      {"type": "thought", "text": ...}
      {"type": "tool_call", "name": ..., "args": {...}}
      {"type": "tool_result", "name": ..., "result": ...}
      {"type": "final", "text": ...}
    Also mutates `history` to append the user/assistant turn.
    """
    client = _client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Only include simple user/assistant text turns from history (skip tool plumbing).
    for turn in history:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    for step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        # No tool calls -> we're done
        if not msg.tool_calls:
            final_text = msg.content or ""
            yield {"type": "final", "text": final_text}
            history.append({"role": "user", "content": user_message})
            history.append({"role": "assistant", "content": final_text})
            return

        # Otherwise: execute every tool call the model requested
        yield {
            "type": "thought",
            "text": f"Step {step + 1}: model wants to call "
            f"{len(msg.tool_calls)} tool(s).",
        }
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            yield {"type": "tool_call", "name": name, "args": args}

            fn = TOOL_FUNCTIONS.get(name)
            result = fn(**args) if fn else f"Unknown tool: {name}"
            yield {"type": "tool_result", "name": name, "result": result}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": name,
                    "content": str(result),
                }
            )

    yield {"type": "final", "text": "(Stopped: reached max reasoning steps.)"}
