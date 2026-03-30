"""Prometheus metric definitions and label sanitization."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Counter, Histogram


def sanitize_label_value(
    raw: str,
    *,
    max_len: int = 48,
    fallback: str = "other",
) -> str:
    """Produce a low-cardinality-safe label fragment."""
    if not raw:
        return fallback
    s = raw.lower().strip()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return fallback
    return s[:max_len]


def namespace_fingerprint(ns: tuple[str, ...] | tuple[()], *, max_depth: int = 4) -> str:
    """Stable short id for LangGraph stream `ns` tuple without exploding cardinality."""
    if not ns:
        return "root"
    clipped = ns[:max_depth]
    h = hashlib.sha256(repr(clipped).encode("utf-8")).hexdigest()[:12]
    return f"d{len(clipped)}_{h}"


@dataclass
class TelemetryMetricSet:
    graph_label: str
    registry: CollectorRegistry
    node_duration: Histogram
    graph_runs_total: Counter
    stream_updates_total: Counter
    llm_tokens_total: Counter
    llm_calls_total: Counter
    llm_usage_missing_total: Counter
    errors_total: Counter

    @classmethod
    def create(
        cls,
        registry: CollectorRegistry,
        graph_label: str,
        *,
        duration_buckets: tuple[float, ...],
    ) -> TelemetryMetricSet:
        g = sanitize_label_value(graph_label, max_len=32, fallback="unknown")
        return cls(
            graph_label=g,
            registry=registry,
            node_duration=Histogram(
                "langgraph_node_duration_seconds",
                "Wall-clock duration between LangGraph stream update events per node",
                ["graph", "node", "namespace"],
                buckets=duration_buckets,
                registry=registry,
            ),
            graph_runs_total=Counter(
                "langgraph_graph_runs_total",
                "Completed LangGraph runs observed by telemetry",
                ["graph", "status"],
                registry=registry,
            ),
            stream_updates_total=Counter(
                "langgraph_stream_updates_total",
                "Number of stream chunks with type=updates",
                ["graph"],
                registry=registry,
            ),
            llm_tokens_total=Counter(
                "langgraph_llm_tokens_total",
                "LLM tokens reported at on_llm_end when usage metadata exists",
                ["graph", "token_type"],
                registry=registry,
            ),
            llm_calls_total=Counter(
                "langgraph_llm_calls_total",
                "LLM invocations seen at on_llm_end",
                ["graph"],
                registry=registry,
            ),
            llm_usage_missing_total=Counter(
                "langgraph_llm_usage_missing_total",
                "LLM invocations without usable token usage metadata",
                ["graph"],
                registry=registry,
            ),
            errors_total=Counter(
                "langgraph_errors_total",
                "Telemetry or task failures observed in stream processing",
                ["graph", "error_class"],
                registry=registry,
            ),
        )
