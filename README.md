# 🤖 Smart Task Assistant

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://youssefsalehsmartbot.streamlit.app/)

🚀 **Live demo:** https://youssefsalehsmartbot.streamlit.app/

A tiny demo combining **Generative AI** and **Agentic Engineering**.

## What it shows
- **GenAI**: An LLM (OpenAI `gpt-4o-mini`) generates natural-language replies.
- **Agentic loop**: The LLM autonomously decides which tools to call to
  fulfill the user's request, observes the results, and iterates.
- **Tools**: `get_current_time`, `calculate`, `get_weather`,
  `add_todo`, `list_todos`, `complete_todo`.
- **Transparency**: The UI shows the agent's reasoning trace —
  every tool call and every result — so non-technical viewers can
  *see* the agent thinking.

## Architecture

```
┌──────────┐   prompt   ┌──────────────┐   tool call   ┌─────────┐
│   User   │──────────► │   LLM brain  │ ────────────► │  Tools  │
└──────────┘            │ (gpt-4o-mini)│ ◄──────────── │ (Python)│
       ▲                └──────┬───────┘   tool result └─────────┘
       │  final answer         │
       └───────────────────────┘   (loop until done)
```

## Run it

```powershell
cd smart-task-assistant
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env       # then edit .env and add your OPENAI_API_KEY
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Demo prompts for your checking
1. *"What's the weather in Tokyo right now?"* → calls `get_weather`.
2. *"Add 'prepare slides for Monday' to my todos."* → calls `add_todo`.
3. *"What is sqrt(144) + 25 * 3?"* → calls `calculate`.
4. *"What's the weather in Paris and add 'pack umbrella' to my todo list."*
   → calls **two tools in sequence** — this is the agentic magic.
5. *"Show my todos and mark task 1 done."* → calls `list_todos`, then `complete_todo`.
