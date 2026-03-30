"""Optional WSGI /metrics server for local demos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import REGISTRY, start_wsgi_server

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry


def start_metrics_server(
    port: int = 9100,
    addr: str = "0.0.0.0",
    *,
    registry: CollectorRegistry | None = None,
) -> None:
    """Start a blocking WSGI server that exposes ``/metrics`` for Prometheus scraping."""
    reg = registry or REGISTRY
    start_wsgi_server(port, addr=addr, registry=reg)
