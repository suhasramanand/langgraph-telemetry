"""Run many concurrent Groq graph turns to drive Prometheus / dashboard (same :9100 metrics)."""

from __future__ import annotations

import os
import threading
import time

from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from langgraph_telemetry import (
    TelemetryConfig,
    TelemetryStreamBridge,
    build_telemetry,
    merge_callbacks,
    start_metrics_server,
)

PROMPTS = [
    "One word: a color.",
    "Reply with a single digit only: 3+4.",
    "Say hi in 3 words.",
    "Capital of Japan — one word.",
    "Name any animal, one word.",
]


def worker(
    wid: int,
    graph: object,
    bridge: TelemetryStreamBridge,
    run_cfg: dict,
    stop: threading.Event,
    sleep_s: float,
) -> None:
    i = wid  # stagger prompt selection
    while not stop.is_set():
        msg = HumanMessage(content=PROMPTS[i % len(PROMPTS)])
        try:
            for _ in bridge.stream(graph, {"messages": [msg]}, config=run_cfg):
                pass
        except Exception as e:
            err = str(e)
            print(f"[worker {wid}] {e}", flush=True)
            # Groq free tier is ~30 RPM; back off on rate limits.
            if "429" in err or "rate_limit" in err.lower():
                if stop.wait(4.0):
                    break
        i += 1
        if stop.wait(sleep_s):
            break


def main() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("Set GROQ_API_KEY. See README.md")

    # Defaults keep ~30 Groq RPM total (free tier): e.g. 2 workers × ~1 req / 4s ≈ 30/min.
    workers = max(1, int(os.environ.get("LIVE_TRAFFIC_WORKERS", "2")))
    sleep_s = float(os.environ.get("LIVE_TRAFFIC_SLEEP_SEC", "4"))
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
        prompt="You are a concise assistant. Reply as briefly as possible.",
        name="groq_chat_agent",
    )

    _metrics, bridge, handler = build_telemetry(TelemetryConfig(graph_name="groq_chat_agent"))
    run_cfg = merge_callbacks(None, handler)

    stop = threading.Event()
    threads: list[threading.Thread] = []
    for w in range(workers):
        t = threading.Thread(
            target=worker,
            name=f"traffic-{w}",
            args=(w, graph, bridge, run_cfg, stop, sleep_s),
            daemon=True,
        )
        t.start()
        threads.append(t)

    print(
        f"Live traffic: {workers} workers, {sleep_s}s between turns each → "
        f"metrics http://127.0.0.1:{port}/metrics (Ctrl+C to stop)",
        flush=True,
    )
    try:
        while True:
            time.sleep(30)
            print(f"[heartbeat] {workers} workers still running", flush=True)
    except KeyboardInterrupt:
        print("stopping…", flush=True)
        stop.set()
    for t in threads:
        t.join(timeout=3)
    print("stopped", flush=True)


if __name__ == "__main__":
    main()
