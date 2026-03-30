"""LangChain callback handler for LLM token usage metrics."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from langgraph_telemetry.metrics import TelemetryMetricSet
from langgraph_telemetry.types import TelemetryConfig


class TelemetryCallbackHandler(BaseCallbackHandler):
    """Record LLM token counters from ``on_llm_end`` (usage metadata when present)."""

    def __init__(
        self,
        config: TelemetryConfig | None = None,
        *,
        graph_name: str | None = None,
        metrics: TelemetryMetricSet | None = None,
    ) -> None:
        super().__init__()
        cfg = config or TelemetryConfig(graph_name=graph_name)
        if graph_name is not None:
            cfg = TelemetryConfig(
                graph_name=graph_name,
                registry=cfg.registry,
                label_policy=cfg.label_policy,
                duration_buckets=cfg.duration_buckets,
                handler_llm_only=cfg.handler_llm_only,
            )
        self._metrics = metrics or TelemetryMetricSet.create(
            cfg.registry,
            cfg.graph_name or "unknown",
            duration_buckets=cfg.duration_buckets,
        )

    @property
    def metrics(self) -> TelemetryMetricSet:
        return self._metrics

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self._metrics.llm_calls_total.labels(graph=self._metrics.graph_label).inc()
        usage: dict[str, Any] = {}
        if response.llm_output and isinstance(response.llm_output, dict):
            raw = response.llm_output.get("token_usage")
            if isinstance(raw, dict):
                usage = raw
        if not usage:
            self._metrics.llm_usage_missing_total.labels(graph=self._metrics.graph_label).inc()
            return

        g = self._metrics.graph_label
        prompt = usage.get("prompt_tokens") or usage.get("input_tokens")
        completion = usage.get("completion_tokens") or usage.get("output_tokens")
        total = usage.get("total_tokens")

        if prompt is not None:
            self._metrics.llm_tokens_total.labels(graph=g, token_type="prompt").inc(int(prompt))
        if completion is not None:
            self._metrics.llm_tokens_total.labels(graph=g, token_type="completion").inc(int(completion))
        if total is not None:
            self._metrics.llm_tokens_total.labels(graph=g, token_type="total").inc(int(total))


def callbacks_config(*handlers: BaseCallbackHandler) -> dict[str, list[BaseCallbackHandler]]:
    """Build a LangGraph/LangChain ``config`` fragment for callbacks."""
    return {"callbacks": list(handlers)}


def merge_callbacks(
    base: dict[str, Any] | None,
    *handlers: BaseCallbackHandler,
) -> dict[str, Any]:
    """Merge telemetry handlers into an existing runnable config."""
    out: dict[str, Any] = dict(base or {})
    existing = list(out.get("callbacks") or [])
    out["callbacks"] = existing + list(handlers)
    return out
