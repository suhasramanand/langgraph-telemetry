"""LangGraph + Groq chat agent with Prometheus metrics (stream + LLM tokens)."""

from __future__ import annotations

import os
import threading
import time

from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from langgraph_telemetry import (
    TelemetryConfig,
    build_telemetry,
    merge_callbacks,
    start_metrics_server,
)

PROMPTS = [
    "Reply with exactly one short sentence: what is 7+5?",
    "Name any color in two words or fewer.",
    "Say hello as a pirate in one line.",
    "What is the capital of France? One phrase.",
]


def _last_ai_snippet(chunk: object) -> str | None:
    if not isinstance(chunk, dict) or chunk.get("type") != "updates":
        return None
    data = chunk.get("data")
    if not isinstance(data, dict):
        return None
    for _node, delta in data.items():
        if not isinstance(delta, dict):
            continue
        msgs = delta.get("messages")
        if not isinstance(msgs, list):
            continue
        for m in reversed(msgs):
            if isinstance(m, AIMessage):
                text = m.content
                if isinstance(text, str) and text.strip():
                    return text.strip()[:240]
                if isinstance(text, list):
                    flat = "".join(
                        str(p.get("text", "")) for p in text if isinstance(p, dict) and p.get("type") == "text"
                    )
                    if flat.strip():
                        return flat.strip()[:240]
    return None


def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit(
            "Set GROQ_API_KEY in the environment. Get a key at https://console.groq.com/"
        )

    port = int(os.environ.get("METRICS_PORT", "9100"))
    threading.Thread(
        target=lambda: start_metrics_server(port, addr="0.0.0.0"),
        name="metrics-wsgi",
        daemon=True,
    ).start()
    time.sleep(0.25)

    model_name = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    model = ChatGroq(model=model_name, temperature=0)
    graph = create_react_agent(
        model,
        [],
        prompt="You are a concise assistant. Keep answers short.",
        name="groq_chat_agent",
    )

    _metrics, bridge, handler = build_telemetry(TelemetryConfig(graph_name="groq_chat_agent"))
    run_cfg = merge_callbacks(None, handler)

    sleep_s = float(os.environ.get("AGENT_SLEEP_SEC", "4"))
    print(
        f"langgraph-telemetry: metrics on http://127.0.0.1:{port}/metrics "
        f"(Groq model={model_name}, Ctrl+C to stop)"
    )
    i = 0
    try:
        while True:
            msg = HumanMessage(content=PROMPTS[i % len(PROMPTS)])
            print(f"--- turn {i + 1}: {msg.content[:70]}...")
            last_reply: str | None = None
            for chunk in bridge.stream(graph, {"messages": [msg]}, config=run_cfg):
                snippet = _last_ai_snippet(chunk)
                if snippet:
                    last_reply = snippet
            if last_reply:
                print(f"    → {last_reply}")
            else:
                print("    → (no AI text in stream; check logs / model response)")
            i += 1
            time.sleep(sleep_s)
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
