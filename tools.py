"""
Tools the agent can call.

Each tool is a plain Python function. The `TOOLS_SCHEMA` below describes them
to the LLM so it knows when and how to invoke them. This is the "Agentic" part:
the LLM decides which tool to call based on the user's intent.
"""
from __future__ import annotations

import datetime as _dt
import math
from typing import Any

import requests

# ---------- In-memory "database" for the to-do list ----------
# In production you would back this with SQL, Cosmos DB, etc.
_TODO_LIST: list[dict[str, Any]] = []


# ---------- Tool implementations ----------
def get_current_time() -> str:
    """Return the current local date and time as a string."""
    return _dt.datetime.now().strftime("%A, %d %B %Y %H:%M:%S")


def calculate(expression: str) -> str:
    """Safely evaluate a basic math expression (e.g. '2 * (3 + 4)')."""
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)  # noqa: S307
        return f"{expression} = {result}"
    except Exception as ex:  # pragma: no cover
        return f"Could not evaluate '{expression}': {ex}"


def get_weather(city: str) -> str:
    """Get current weather for a city using the free Open-Meteo API (no key)."""
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        ).json()
        if not geo.get("results"):
            return f"Could not find city '{city}'."
        loc = geo["results"][0]
        lat, lon, name = loc["latitude"], loc["longitude"], loc["name"]
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=10,
        ).json()
        cur = wx["current_weather"]
        return (
            f"Weather in {name}: {cur['temperature']}°C, "
            f"wind {cur['windspeed']} km/h."
        )
    except Exception as ex:
        return f"Weather lookup failed: {ex}"


def add_todo(task: str) -> str:
    _TODO_LIST.append({"task": task, "done": False})
    return f"Added task: '{task}'. You now have {len(_TODO_LIST)} task(s)."


def list_todos() -> str:
    if not _TODO_LIST:
        return "Your to-do list is empty."
    lines = [
        f"{i + 1}. [{'x' if t['done'] else ' '}] {t['task']}"
        for i, t in enumerate(_TODO_LIST)
    ]
    return "Your to-do list:\n" + "\n".join(lines)


def complete_todo(index: int) -> str:
    i = index - 1
    if i < 0 or i >= len(_TODO_LIST):
        return f"Invalid task number {index}."
    _TODO_LIST[i]["done"] = True
    return f"Marked task {index} as done: '{_TODO_LIST[i]['task']}'."


# ---------- Dispatcher ----------
TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_weather": get_weather,
    "add_todo": add_todo,
    "list_todos": list_todos,
    "complete_todo": complete_todo,
}


# ---------- Schema sent to the LLM ----------
TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a math expression like '2*(3+4)' or 'sqrt(16)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name."}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "Add a new task to the to-do list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description."}
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_todos",
            "description": "List all tasks on the to-do list.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_todo",
            "description": "Mark a to-do task as done by its 1-based index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "1-based index of the task to complete.",
                    }
                },
                "required": ["index"],
            },
        },
    },
]
