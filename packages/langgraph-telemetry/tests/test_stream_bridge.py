from __future__ import annotations

from typing import TypedDict

import pytest
from langgraph.graph import END, START, StateGraph
from prometheus_client import CollectorRegistry

from langgraph_telemetry.stream_bridge import TelemetryStreamBridge
from langgraph_telemetry.types import TelemetryConfig


class St(TypedDict):
    x: int


def _compile_simple():
    def n1(state: St) -> dict[str, int]:
        return {"x": state["x"] + 1}

    g = StateGraph(St)
    g.add_node("n1", n1)
    g.add_edge(START, "n1")
    g.add_edge("n1", END)
    return g.compile()


def test_bridge_records_updates_and_run(registry: CollectorRegistry) -> None:
    cfg = TelemetryConfig(registry=registry, graph_name="test_graph")
    bridge = TelemetryStreamBridge(config=cfg)
    graph = _compile_simple()
    list(bridge.stream(graph, {"x": 0}))
    assert registry.get_sample_value("langgraph_graph_runs_total", {"graph": "test_graph", "status": "success"}) == 1.0
    assert registry.get_sample_value("langgraph_stream_updates_total", {"graph": "test_graph"}) == 1.0


def test_bridge_records_error(registry: CollectorRegistry) -> None:
    class St2(TypedDict):
        x: int

    def boom(state: St2) -> dict[str, int]:
        raise RuntimeError("nope")

    g = StateGraph(St2)
    g.add_node("boom", boom)
    g.add_edge(START, "boom")
    g.add_edge("boom", END)
    compiled = g.compile()
    cfg = TelemetryConfig(registry=registry, graph_name="e")
    bridge = TelemetryStreamBridge(config=cfg)
    with pytest.raises(RuntimeError):
        list(bridge.stream(compiled, {"x": 0}))
    assert registry.get_sample_value("langgraph_graph_runs_total", {"graph": "e", "status": "error"}) == 1.0
    assert registry.get_sample_value("langgraph_errors_total", {"graph": "e", "error_class": "stream"}) == 1.0
