"""Configuration types for langgraph-telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from prometheus_client import REGISTRY, CollectorRegistry


@dataclass
class LabelPolicy:
    """Controls how LangGraph namespaces and node names map to Prometheus labels."""

    max_node_len: int = 48
    namespace_max_depth: int = 4


@dataclass
class TelemetryConfig:
    """Shared settings for stream bridge and callback handler."""

    graph_name: str | None = None
    registry: CollectorRegistry = field(default_factory=lambda: REGISTRY)
    label_policy: LabelPolicy = field(default_factory=LabelPolicy)
    duration_buckets: tuple[float, ...] = (
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        25.0,
        60.0,
    )
    # When True, callback handler records LLM metrics only (no duplicate node histograms).
    handler_llm_only: bool = True


# Stream chunk shape when using LangGraph stream(..., version="v2").
StreamPart = dict[str, Any]
