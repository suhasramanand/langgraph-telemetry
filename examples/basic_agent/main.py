"""Emit sample LangGraph metrics on :9100/metrics for Prometheus scraping."""

from __future__ import annotations

import threading
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from langgraph_telemetry import TelemetryConfig, TelemetryStreamBridge, start_metrics_server


class State(TypedDict):
    n: int


def bump(state: State) -> dict[str, int]:
    return {"n": state["n"] + 1}


def build_graph():
    g = StateGraph(State)
    g.add_node("bump", bump)
    g.add_edge(START, "bump")
    g.add_edge("bump", END)
    return g.compile()


def main() -> None:
    threading.Thread(
        target=lambda: start_metrics_server(9100, addr="0.0.0.0"),
        name="metrics-wsgi",
        daemon=True,
    ).start()
    time.sleep(0.25)

    graph = build_graph()
    cfg = TelemetryConfig(graph_name="basic_agent")
    bridge = TelemetryStreamBridge(config=cfg)
    print("langgraph-telemetry: metrics on http://127.0.0.1:9100/metrics (Ctrl+C to stop)")
    try:
        while True:
            list(bridge.stream(graph, {"n": 0}))
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("stopped")


if __name__ == "__main__":
    main()
