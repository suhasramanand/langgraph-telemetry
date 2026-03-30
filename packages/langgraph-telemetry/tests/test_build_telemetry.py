from __future__ import annotations

from prometheus_client import CollectorRegistry

from langgraph_telemetry import build_telemetry
from langgraph_telemetry.types import TelemetryConfig


def test_build_telemetry_shares_metrics() -> None:
    reg = CollectorRegistry()
    cfg = TelemetryConfig(registry=reg, graph_name="g")
    metrics, bridge, handler = build_telemetry(config=cfg)
    assert metrics is bridge.metrics
    assert metrics is handler.metrics
