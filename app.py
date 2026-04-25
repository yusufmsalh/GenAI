"""
Streamlit UI for the Smart Task Assistant.

Run with:    streamlit run app.py
"""
from __future__ import annotations

import traceback

import streamlit as st
from dotenv import load_dotenv

from agent import run_agent

load_dotenv()

st.set_page_config(page_title="Smart Task Assistant", page_icon="🤖")
st.title("🤖 Smart Task Assistant")
st.caption("A demo of Generative AI + Agentic Engineering (LLM + Tools + Loop)")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "- **GenAI**: an LLM understands your message.\n"
        "- **Agentic**: the LLM picks tools to actually *do* things.\n"
        "- **Tools available:** time, math, weather, to-do list.\n\n"
        "**Try:**\n"
        "- *What's the weather in Tokyo?*\n"
        "- *Add 'buy milk' to my todos*\n"
        "- *What's sqrt(144) + 7?*\n"
        "- *Weather in Paris and add 'pack umbrella'*"
    )

if "history" not in st.session_state:
    st.session_state.history = []

# Render previous chat
for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

prompt = st.chat_input("Ask me anything…")
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        trace_box = st.expander("🔎 Agent reasoning trace", expanded=True)
        final_placeholder = st.empty()
        final_text = ""

        try:
            for event in run_agent(prompt, st.session_state.history):
                if event["type"] == "thought":
                    trace_box.markdown(f"💭 {event['text']}")
                elif event["type"] == "tool_call":
                    trace_box.markdown(
                        f"🛠️ **Calling tool** `{event['name']}` "
                        f"with `{event['args']}`"
                    )
                elif event["type"] == "tool_result":
                    trace_box.markdown(
                        f"✅ **Result from** `{event['name']}`: {event['result']}"
                    )
                elif event["type"] == "final":
                    final_text = event["text"]
                    final_placeholder.markdown(final_text)
        except Exception as ex:
            tb = traceback.format_exc()
            print(tb)  # full traceback in the terminal
            final_placeholder.error(f"Error: {type(ex).__name__}: {ex}")
            with st.expander("🐞 Full traceback", expanded=False):
                st.code(tb)
