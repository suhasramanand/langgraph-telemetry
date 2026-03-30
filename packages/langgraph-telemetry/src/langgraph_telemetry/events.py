"""Optional hooks for low-level LangGraph event APIs.

Primary integration: :class:`~langgraph_telemetry.stream_bridge.TelemetryStreamBridge`
with ``graph.stream`` / ``graph.astream`` and ``version="v2"`` (see LangGraph
`Streaming <https://docs.langchain.com/oss/python/langgraph/streaming>`_ docs).

If you must use ``astream_events`` instead of ``stream``, mirror the same
``StreamPart``-shaped payloads (``type``, ``ns``, ``data``) and reuse
:class:`~langgraph_telemetry.metrics.TelemetryMetricSet` with custom wiring,
or open an issue to request a first-class adapter.
"""

from __future__ import annotations

__all__: list[str] = []
