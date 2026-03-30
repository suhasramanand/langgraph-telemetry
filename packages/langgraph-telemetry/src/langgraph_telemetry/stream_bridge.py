"""Wrap LangGraph v2 streams and record Prometheus metrics."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Any

from langgraph_telemetry.metrics import TelemetryMetricSet, namespace_fingerprint, sanitize_label_value
from langgraph_telemetry.types import StreamPart, TelemetryConfig


class TelemetryStreamBridge:
    """Consume `graph.stream` / `graph.astream` (``version=\"v2\"``) and update metrics."""

    def __init__(
        self,
        config: TelemetryConfig | None = None,
        *,
        graph_name: str | None = None,
        metrics: TelemetryMetricSet | None = None,
    ) -> None:
        cfg = config or TelemetryConfig(graph_name=graph_name)
        if graph_name is not None:
            cfg = TelemetryConfig(
                graph_name=graph_name,
                registry=cfg.registry,
                label_policy=cfg.label_policy,
                duration_buckets=cfg.duration_buckets,
                handler_llm_only=cfg.handler_llm_only,
            )
        self._cfg = cfg
        self._metrics = metrics or TelemetryMetricSet.create(
            cfg.registry,
            cfg.graph_name or "unknown",
            duration_buckets=cfg.duration_buckets,
        )
        self._policy = cfg.label_policy

    @property
    def metrics(self) -> TelemetryMetricSet:
        return self._metrics

    def stream(
        self,
        graph: Any,
        input_data: Mapping[str, Any] | Any,
        *,
        config: dict[str, Any] | None = None,
        stream_mode: list[str] | None = None,
        **stream_kw: Any,
    ) -> Iterator[dict[str, Any]]:
        """Yield stream chunks from ``graph.stream`` and record metrics."""
        modes = list(stream_mode) if stream_mode else ["updates"]
        if "updates" not in modes:
            modes.append("updates")
        use_tasks = "tasks" in modes
        self._task_starts: dict[str, float] = {}
        last_mono: float | None = None
        status = "success"
        try:
            iterable = graph.stream(
                input_data,
                config=config,
                stream_mode=modes,
                version="v2",
                **stream_kw,
            )
            for chunk in iterable:
                last_mono = self._process_chunk(
                    chunk,
                    last_mono=last_mono,
                    use_task_durations=use_tasks,
                )
                yield chunk
        except BaseException:
            status = "error"
            self._metrics.errors_total.labels(
                graph=self._metrics.graph_label,
                error_class="stream",
            ).inc()
            raise
        finally:
            self._metrics.graph_runs_total.labels(
                graph=self._metrics.graph_label,
                status=status,
            ).inc()

    async def astream(
        self,
        graph: Any,
        input_data: Mapping[str, Any] | Any,
        *,
        config: dict[str, Any] | None = None,
        stream_mode: list[str] | None = None,
        **stream_kw: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        modes = list(stream_mode) if stream_mode else ["updates"]
        if "updates" not in modes:
            modes.append("updates")
        use_tasks = "tasks" in modes
        self._task_starts = {}
        last_mono: float | None = None
        status = "success"
        try:
            async for chunk in graph.astream(
                input_data,
                config=config,
                stream_mode=modes,
                version="v2",
                **stream_kw,
            ):
                last_mono = self._process_chunk(
                    chunk,
                    last_mono=last_mono,
                    use_task_durations=use_tasks,
                )
                yield chunk
        except BaseException:
            status = "error"
            self._metrics.errors_total.labels(
                graph=self._metrics.graph_label,
                error_class="stream",
            ).inc()
            raise
        finally:
            self._metrics.graph_runs_total.labels(
                graph=self._metrics.graph_label,
                status=status,
            ).inc()

    def _process_chunk(
        self,
        chunk: StreamPart,
        *,
        last_mono: float | None,
        use_task_durations: bool,
    ) -> float | None:
        if not isinstance(chunk, dict):
            return last_mono
        ctype = chunk.get("type")
        ns_raw = chunk.get("ns") or ()
        ns_t: tuple[str, ...] = tuple(ns_raw) if ns_raw else ()
        ns_label = namespace_fingerprint(ns_t, max_depth=self._policy.namespace_max_depth)

        if ctype == "updates":
            data = chunk.get("data") or {}
            if isinstance(data, dict):
                self._metrics.stream_updates_total.labels(graph=self._metrics.graph_label).inc()
                now = time.monotonic()
                if not use_task_durations and last_mono is not None:
                    dt = now - last_mono
                    for node_name in data:
                        node = sanitize_label_value(
                            str(node_name),
                            max_len=self._policy.max_node_len,
                        )
                        self._metrics.node_duration.labels(
                            graph=self._metrics.graph_label,
                            node=node,
                            namespace=ns_label,
                        ).observe(dt)
                return now

        if ctype == "tasks":
            self._handle_task_chunk(chunk, ns_label, use_task_durations)

        return last_mono

    def _handle_task_chunk(
        self,
        chunk: StreamPart,
        ns_label: str,
        use_task_durations: bool,
    ) -> None:
        data = chunk.get("data")
        if not isinstance(data, dict):
            return
        tid = data.get("id")
        if tid is None:
            return
        tid_str = str(tid)
        is_end = ("result" in data) or (data.get("error") is not None)
        is_start = ("input" in data) and ("result" not in data) and (data.get("error") is None)

        if use_task_durations and is_start:
            self._task_starts[tid_str] = time.monotonic()
        elif is_end:
            started = self._task_starts.pop(tid_str, None)
            if use_task_durations and started is not None:
                dt = time.monotonic() - started
                name = data.get("name") or "unknown"
                node = sanitize_label_value(str(name), max_len=self._policy.max_node_len)
                self._metrics.node_duration.labels(
                    graph=self._metrics.graph_label,
                    node=node,
                    namespace=ns_label,
                ).observe(dt)
            err = data.get("error")
            if err is not None:
                self._metrics.errors_total.labels(
                    graph=self._metrics.graph_label,
                    error_class="task",
                ).inc()
