"""LangGraph-Telemetry: Prometheus metrics for LangGraph runs."""

from __future__ import annotations

from langgraph_telemetry.handler import (
    TelemetryCallbackHandler,
    callbacks_config,
    merge_callbacks,
)
from langgraph_telemetry.metrics import (
    TelemetryMetricSet,
    namespace_fingerprint,
    sanitize_label_value,
)
from langgraph_telemetry.server import start_metrics_server
from langgraph_telemetry.stream_bridge import TelemetryStreamBridge
from langgraph_telemetry.types import LabelPolicy, TelemetryConfig

__all__ = [
    "LabelPolicy",
    "TelemetryCallbackHandler",
    "TelemetryConfig",
    "TelemetryMetricSet",
    "TelemetryStreamBridge",
    "callbacks_config",
    "merge_callbacks",
    "namespace_fingerprint",
    "sanitize_label_value",
    "start_metrics_server",
]


def build_telemetry(
    config: TelemetryConfig | None = None,
    *,
    graph_name: str | None = None,
) -> tuple[TelemetryMetricSet, TelemetryStreamBridge, TelemetryCallbackHandler]:
    """Create a shared :class:`TelemetryMetricSet` plus bridge and callback handler."""
    cfg = config or TelemetryConfig(graph_name=graph_name)
    if graph_name is not None:
        cfg = TelemetryConfig(
            graph_name=graph_name,
            registry=cfg.registry,
            label_policy=cfg.label_policy,
            duration_buckets=cfg.duration_buckets,
            handler_llm_only=cfg.handler_llm_only,
        )
    metrics = TelemetryMetricSet.create(
        cfg.registry,
        cfg.graph_name or "unknown",
        duration_buckets=cfg.duration_buckets,
    )
    return (
        metrics,
        TelemetryStreamBridge(config=cfg, metrics=metrics),
        TelemetryCallbackHandler(config=cfg, metrics=metrics),
    )


__all__ += ["build_telemetry"]
